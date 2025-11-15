"""Telemetry endpoints."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from src.services.telemetry import TelemetryEvent, get_telemetry_service

router = APIRouter()


class TelemetryIngest(BaseModel):
    lobby_id: str
    type: str
    samples: list[float]


@router.post("/events", status_code=202)
async def publish(event: TelemetryIngest) -> None:
    svc = get_telemetry_service()
    svc.publish(
        TelemetryEvent(
            session_id=event.lobby_id,
            source="frontend",
            event_type=event.type,
            payload={"samples": event.samples},
            captured_at=datetime.utcnow(),
        )
    )
