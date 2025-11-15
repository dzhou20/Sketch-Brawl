"""Battle API endpoints."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.services.battle_service import BattleService
from src.workers.battle_worker import celery_app, run_battle_task
from celery.result import AsyncResult

router = APIRouter()
service = BattleService()


class BattleRequest(BaseModel):
    lobby_id: str = Field(..., description="Lobby identifier shared by both players")
    seed: int | None = Field(default=None, description="Optional deterministic seed override")


class CombatantPayload(BaseModel):
    slot: str
    name: str
    element: str
    base_hp: int
    base_attack: int
    skill_power: int
    snapshot: str | None = None
    skills: list[Dict[str, Any]] = Field(default_factory=list)


class RoundSummary(BaseModel):
    round: int
    winner_slot: str
    turns: int
    ko_turn: int | None = None
    total_damage: Dict[str, int]
    hp_remaining: Dict[str, int]


class BattleResponse(BaseModel):
    battle_id: int
    winner_slot: str
    wins: Dict[str, int]
    timeline: list[Dict[str, Any]]
    rounds: list[RoundSummary]
    combatants: list[CombatantPayload]


class BattleJobTicket(BaseModel):
    job_id: str
    status: Literal["queued"]


class BattleJobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "started", "failed", "finished"]
    battle_id: int | None = None
    detail: str | None = None


@router.post("", response_model=BattleResponse)
async def start_battle(payload: BattleRequest) -> BattleResponse:
    try:
        result = service.start_battle(payload.lobby_id, payload.seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BattleResponse(**result)


@router.get("/{battle_id}", response_model=BattleResponse)
async def get_battle(battle_id: int) -> BattleResponse:
    battle = service.get_battle(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    summary = battle.summary or {}
    wins = summary.get("wins") or {}
    rounds = summary.get("rounds") or []
    winner = summary.get("winner_slot") or battle.winner_player_id or ""
    return BattleResponse(
        battle_id=battle.id,
        winner_slot=winner,
        wins=wins,
        timeline=battle.rounds or [],
        rounds=rounds,
        combatants=battle.combatants or [],
    )


@router.post("/async", response_model=BattleJobTicket, status_code=202)
async def start_battle_async(payload: BattleRequest) -> BattleJobTicket:
    task = run_battle_task.delay(payload.lobby_id, payload.seed)
    return BattleJobTicket(job_id=task.id, status="queued")


@router.get("/jobs/{job_id}", response_model=BattleJobStatus)
async def get_battle_job(job_id: str) -> BattleJobStatus:
    result = AsyncResult(job_id, app=celery_app)
    status = result.state.lower()
    detail = None
    battle_id = None
    if status == "success":
        data = result.result or {}
        battle_id = data.get("battle_id")
        status = "finished"
    elif status in {"failure", "failed"}:
        detail = str(result.result)
        status = "failed"
    elif status == "started":
        status = "started"
    else:
        status = "queued"
    return BattleJobStatus(job_id=job_id, status=status, battle_id=battle_id, detail=detail)


@router.get("/{battle_id}/events")
async def stream_battle_events(battle_id: int):
    battle = service.get_battle(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    events = battle.rounds or []

    async def event_generator():
        for event in events:
            payload = json.dumps(event)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0.35)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
