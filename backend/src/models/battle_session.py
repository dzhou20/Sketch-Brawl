"""Battle session, telemetry, and demo artifact models."""
from __future__ import annotations

from typing import Optional

from sqlmodel import Column, Field, SQLModel
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


class BattleSession(SQLModel, table=True):
    __tablename__ = "battle_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    lobby_id: str = Field(index=True)
    rng_seed: str = Field(index=True)
    rounds: list[dict] = Field(sa_column=Column(JSONB))
    winner_player_id: Optional[str] = Field(default=None, index=True)
    replay_uri: Optional[str] = None
    state: str = Field(default="pending", index=True)
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class TelemetryEvent(SQLModel, table=True):
    __tablename__ = "telemetry_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    source: str
    event_type: str = Field(index=True)
    payload: dict = Field(sa_column=Column(JSONB))
    captured_at: Optional[str] = None


class DemoArtifact(SQLModel, table=True):
    __tablename__ = "demo_artifacts"

    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_type: str = Field(index=True)
    version: str
    uri: str
    checksum: str
    generated_from_commit: str
    status: str = Field(default="active")
    created_at: Optional[str] = None
