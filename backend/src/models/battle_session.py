"""Battle session, telemetry, and demo artifact models."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class BattleSession(SQLModel, table=True):
    __tablename__ = "battle_sessions"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    lobby_id: str = Field(index=True)
    rng_seed: str = Field(index=True)
    rounds: list[dict] = Field(sa_column=Column(JSON))
    summary: dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    combatants: list[dict] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    winner_player_id: Optional[str] = Field(default=None, index=True)
    replay_uri: Optional[str] = None
    state: str = Field(default="pending", index=True)
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class TelemetryEvent(SQLModel, table=True):
    __tablename__ = "telemetry_events"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    source: str
    event_type: str = Field(index=True)
    payload: dict = Field(sa_column=Column(JSON))
    captured_at: Optional[str] = None


class DemoArtifact(SQLModel, table=True):
    __tablename__ = "demo_artifacts"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    artifact_type: str = Field(index=True)
    version: str
    uri: str
    checksum: str
    generated_from_commit: str
    status: str = Field(default="active")
    created_at: Optional[str] = None
