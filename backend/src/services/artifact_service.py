"""Service utilities for demo artifact retrieval."""
from __future__ import annotations

from typing import Dict, List, Optional

from sqlmodel import Session, select

from src.infra.database import get_engine
from src.models.battle_session import DemoArtifact


class ArtifactService:
    def __init__(self) -> None:
        self._engine = get_engine()

    def get_latest(self) -> Dict[str, Optional[str]]:
        records = self._load_active()
        latest_by_type = self._dedupe_by_type(records)
        playable = latest_by_type.get("playable_build")
        walkthrough = latest_by_type.get("walkthrough_video")
        offline = latest_by_type.get("offline_bundle")
        version = (
            playable.version
            if playable is not None
            else (walkthrough or offline).version
            if (walkthrough or offline) is not None
            else None
        )
        return {
            "playable_url": playable.uri if playable else None,
            "walkthrough_video_url": walkthrough.uri if walkthrough else None,
            "offline_bundle_url": offline.uri if offline else None,
            "version": version,
        }

    def _load_active(self) -> List[DemoArtifact]:
        with Session(self._engine) as session:
            stmt = (
                select(DemoArtifact)
                .where(DemoArtifact.status == "active")
                .order_by(DemoArtifact.id.desc())
            )
            return list(session.exec(stmt))

    def _dedupe_by_type(
        self, artifacts: List[DemoArtifact]
    ) -> Dict[str, DemoArtifact]:
        result: Dict[str, DemoArtifact] = {}
        for artifact in artifacts:
            if artifact.artifact_type not in result:
                result[artifact.artifact_type] = artifact
        return result
