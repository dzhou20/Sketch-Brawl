"""Doodle upload + inference endpoints."""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.attribute_store import DoodleType, get_attribute_store
from src.services.inference_runner import get_runner
from src.services.telemetry import TelemetryEvent, get_telemetry_service
from src.services.validation import ValidationError, validate_reinforcement

router = APIRouter()
logger = logging.getLogger("api.doodles")


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
    snapshot: str | None = None


class InferenceTicket(BaseModel):
    ticket_id: str
    expires_in: int = 300


class InferenceResult(BaseModel):
    ticket_id: str
    payload: dict[str, Any] | None
    ready: bool
    waiting_for: str | None = None


def _store():
    return get_attribute_store()


def _telemetry():
    return get_telemetry_service()


@router.post("", status_code=202, response_model=InferenceTicket)
async def submit_doodle(request: DoodleRequest) -> InferenceTicket:
    logger.info(
        "doodles.submit start lobby=%s type=%s strokes=%d seed=%s",
        request.lobby_id,
        request.doodle_type,
        len(request.strokes),
        request.seed,
    )
    if request.doodle_type == "reinforcement" and request.metadata:
        try:
            validate_reinforcement(request.metadata)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    runner = get_runner()
    start = time.perf_counter()
    try:
        attributes = runner.predict(
        [stroke.model_dump() for stroke in request.strokes],
        request.seed or int(start),
        doodle_type=request.doodle_type,
        metadata=request.metadata,
        snapshot=request.snapshot,
    )
    except Exception:
        logger.exception(
            "doodles.submit inference_error lobby=%s type=%s", request.lobby_id, request.doodle_type
        )
        raise
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "doodles.submit inference_ok lobby=%s type=%s elapsed_ms=%.2f element=%s seed=%s",
        request.lobby_id,
        request.doodle_type,
        elapsed,
        attributes.get("element"),
        attributes.get("seed"),
    )

    persisted = _store().persist(
        request.lobby_id,
        request.doodle_type,
        attributes,
        metadata=request.metadata or {},
        snapshot=request.snapshot,
    )
    ticket_id = _store().save_ticket(persisted)
    logger.info(
        "doodles.submit persisted lobby=%s type=%s ticket=%s monster_id=%s skill_id=%s",
        request.lobby_id,
        request.doodle_type,
        ticket_id,
        persisted.get("monster_id"),
        persisted.get("skill_id"),
    )

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
    store = _store()
    payload = store.get_ticket(ticket_id)
    if not payload:
        raise HTTPException(status_code=404, detail="ticket not found")
    ready, waiting_for = store.ready_for_client(payload)
    result_payload = payload if ready else None
    return InferenceResult(
        ticket_id=ticket_id,
        payload=result_payload,
        ready=ready,
        waiting_for=waiting_for,
    )
