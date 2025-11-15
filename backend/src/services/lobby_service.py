"""Lobby service handles invite links and readiness state using Redis."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

import redis

from src.config import get_settings

Role = Literal["player", "judge", "spectator"]
Status = Literal["waiting", "ready", "battling", "completed"]


@dataclass
class Lobby:
    id: str
    invite_code: str
    status: Status
    created_at: str


class LobbyService:
    def __init__(self) -> None:
        self._redis = redis.from_url(get_settings().redis_url, decode_responses=True)
        self._ttl = 60 * 60  # 1h per lobby unless refreshed

    def create_or_join(self, invite_code: str, role: Role) -> Lobby:
        lobby_id = self._redis.get(self._invite_key(invite_code))
        if not lobby_id:
            lobby_id = uuid.uuid4().hex
            lobby_payload = {
                "id": lobby_id,
                "invite_code": invite_code,
                "status": "waiting",
                "created_at": datetime.utcnow().isoformat(),
                "players": json.dumps([]),
            }
            self._redis.hset(self._lobby_key(lobby_id), mapping=lobby_payload)
            self._redis.set(self._invite_key(invite_code), lobby_id, ex=self._ttl)
        self._redis.expire(self._lobby_key(lobby_id), self._ttl)
        self._redis.expire(self._invite_key(invite_code), self._ttl)
        return self._hydrate(lobby_id)

    def heartbeat(self, lobby_id: str, role: Role) -> Lobby:
        if not self._redis.exists(self._lobby_key(lobby_id)):
            raise ValueError("Lobby not found")
        self._redis.expire(self._lobby_key(lobby_id), self._ttl)
        return self._hydrate(lobby_id)

    def mark_ready(self, lobby_id: str) -> Lobby:
        key = self._lobby_key(lobby_id)
        if not self._redis.exists(key):
            raise ValueError("Lobby not found")
        self._redis.hset(key, "status", "ready")
        self._redis.expire(key, self._ttl)
        return self._hydrate(lobby_id)

    def _hydrate(self, lobby_id: str) -> Lobby:
        data = self._redis.hgetall(self._lobby_key(lobby_id))
        if not data:
            raise ValueError("Lobby expired")
        return Lobby(
            id=data["id"],
            invite_code=data["invite_code"],
            status=data.get("status", "waiting"),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
        )

    def _lobby_key(self, lobby_id: str) -> str:
        return f"lobby:{lobby_id}"

    def _invite_key(self, invite_code: str) -> str:
        return f"invite:{invite_code}"


_service: LobbyService | None = None


def get_lobby_service() -> LobbyService:
    global _service
    if _service is None:
        _service = LobbyService()
    return _service
