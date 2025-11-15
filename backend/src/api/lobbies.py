"""Lobby endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.lobby_service import LobbyService, get_lobby_service, Role

router = APIRouter()


class LobbyRequest(BaseModel):
    invite_code: str = Field(min_length=2)
    role: Role = Field(default="player")
    display_name: str | None = None


class LobbyResponse(BaseModel):
    id: str
    invite_code: str
    status: str
    created_at: str


def _service() -> LobbyService:
    return get_lobby_service()


@router.post("", response_model=LobbyResponse)
async def create_or_join_lobby(payload: LobbyRequest) -> LobbyResponse:
    try:
        lobby = _service().create_or_join(payload.invite_code, payload.role)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LobbyResponse(**lobby.__dict__)


@router.post("/{lobby_id}/heartbeat", response_model=LobbyResponse)
async def heartbeat(lobby_id: str, payload: LobbyRequest) -> LobbyResponse:
    try:
        lobby = _service().heartbeat(lobby_id, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LobbyResponse(**lobby.__dict__)


@router.post("/{lobby_id}/ready", response_model=LobbyResponse)
async def mark_ready(lobby_id: str) -> LobbyResponse:
    try:
        lobby = _service().mark_ready(lobby_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LobbyResponse(**lobby.__dict__)
