"""Doodle upload + inference endpoints."""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.attribute_store import DoodleType, get_attribute_store
from src.services.inference_runner import get_runner
from src.services.telemetry import TelemetryEvent, get_telemetry_service
from src.services.validation import ValidationError, validate_reinforcement

router = APIRouter()


class Stroke(BaseModel):
    x: float
    y: float
    pressure: float | None = None
    timestamp: float


class DoodleRequest(BaseModel):
    lobby_id: str
    doodle_type: DoodleType
    strokes: list[Stroke]
    metadata: dict[str, Any] | None = None
    seed: int | None = None


class InferenceTicket(BaseModel):
    ticket_id: str
    expires_in: int = 300


class InferenceResult(BaseModel):
    ticket_id: str
    payload: dict[str, Any]


def _store():
    return get_attribute_store()


def _telemetry():
    return get_telemetry_service()


@router.post("", status_code=202, response_model=InferenceTicket)
async def submit_doodle(request: DoodleRequest) -> InferenceTicket:
    if request.doodle_type == "reinforcement" and request.metadata:
        try:
            validate_reinforcement(request.metadata)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    runner = get_runner()
    start = time.perf_counter()
    attributes = runner.predict([stroke.model_dump() for stroke in request.strokes], request.seed or int(start))
    elapsed = (time.perf_counter() - start) * 1000

    persisted = _store().persist(request.lobby_id, request.doodle_type, attributes)
    ticket_id = _store().save_ticket(persisted)

    _telemetry().publish(
        TelemetryEvent(
            session_id=request.lobby_id,
            source="backend",
            event_type="inference_time",
            payload={"ms": elapsed, "ticket": ticket_id},
            captured_at=datetime.utcnow(),
        )
    )

    return InferenceTicket(ticket_id=ticket_id)


@router.get("/{ticket_id}", response_model=InferenceResult)
async def get_doodle(ticket_id: str) -> InferenceResult:
    payload = _store().get_ticket(ticket_id)
    if not payload:
        raise HTTPException(status_code=404, detail="ticket not found")
    return InferenceResult(ticket_id=ticket_id, payload=payload)
