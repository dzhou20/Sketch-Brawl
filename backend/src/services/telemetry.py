"""Telemetry aggregation service."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any

import redis

from src.config import get_settings


@dataclass
class TelemetryEvent:
    session_id: str
    source: str
    event_type: str
    payload: dict[str, Any]
    captured_at: datetime


class TelemetryService:
    def __init__(self) -> None:
        self._redis = redis.from_url(get_settings().redis_url)

    def publish(self, event: TelemetryEvent) -> None:
        channel = f"telemetry:{event.event_type}"
        payload_value: str | int | float
        if isinstance(event.payload, (dict, list)):
            payload_value = json.dumps(event.payload)
        elif isinstance(event.payload, (str, int, float)):
            payload_value = event.payload
        else:
            payload_value = str(event.payload)
        self._redis.xadd(
            channel,
            {
                "session": event.session_id,
                "source": event.source,
                "captured_at": event.captured_at.isoformat(),
                "payload": payload_value,
            },
        )

    def aggregate_latency(self, session_id: str) -> dict[str, float]:
        channel = "telemetry:canvas_latency"
        entries = self._redis.xrange(channel, count=100)
        samples: list[float] = []
        for entry in entries:
            if entry[1].get(b"session") != session_id.encode():
                continue
            payload_bytes = entry[1][b"payload"]
            payload_text = payload_bytes.decode()
            value: float | None = None
            try:
                value = float(payload_text)
            except ValueError:
                try:
                    data = json.loads(payload_text)
                except json.JSONDecodeError:
                    data = None
                if isinstance(data, (int, float, str)):
                    try:
                        value = float(data)
                    except (TypeError, ValueError):
                        value = None
                elif isinstance(data, dict):
                    for key in ("ms", "value", "latency", "fps"):
                        candidate = data.get(key)
                        if isinstance(candidate, (int, float, str)):
                            try:
                                value = float(candidate)
                                break
                            except (TypeError, ValueError):
                                continue
            if value is not None:
                samples.append(value)
        if not samples:
            return {"p95": 0.0, "min_fps": 0.0}
        samples.sort()
        idx = int(len(samples) * 0.95) - 1
        return {"p95": samples[max(idx, 0)], "min_fps": min(samples)}


_service: TelemetryService | None = None


def get_telemetry_service() -> TelemetryService:
    global _service
    if _service is None:
        _service = TelemetryService()
    return _service
