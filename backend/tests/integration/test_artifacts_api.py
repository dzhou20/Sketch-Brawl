"""Integration tests for /artifacts/latest API."""
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, delete

from src.api import artifacts
from src.api.main import app
from src.infra import database
from src.models.battle_session import DemoArtifact
from src.services.artifact_service import ArtifactService

test_engine = create_engine(
    "sqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

database._engine = test_engine
SQLModel.metadata.create_all(test_engine)
artifacts.service = ArtifactService()
client = TestClient(app)


def _seed_demo_artifacts() -> None:
    _clear_artifacts()
    with Session(test_engine) as session:
        session.add(
            DemoArtifact(
                artifact_type="playable_build",
                version="0.2.0",
                uri="https://demo.example/playable",
                checksum="abc123",
                generated_from_commit="deadbeef",
                status="active",
            )
        )
        session.add(
            DemoArtifact(
                artifact_type="walkthrough_video",
                version="0.2.0",
                uri="https://demo.example/video",
                checksum="def456",
                generated_from_commit="deadbeef",
                status="active",
            )
        )
        session.add(
            DemoArtifact(
                artifact_type="offline_bundle",
                version="0.2.0",
                uri="https://demo.example/offline.zip",
                checksum="ghi789",
                generated_from_commit="deadbeef",
                status="active",
            )
        )
        session.commit()


def _clear_artifacts() -> None:
    with Session(test_engine) as session:
        session.exec(delete(DemoArtifact))
        session.commit()


def test_latest_artifacts_returns_active_payload():
    _seed_demo_artifacts()

    resp = client.get("/artifacts/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["playable_url"] == "https://demo.example/playable"
    assert body["walkthrough_video_url"] == "https://demo.example/video"
    assert body["offline_bundle_url"] == "https://demo.example/offline.zip"
    assert body["version"] == "0.2.0"


def test_latest_artifacts_handles_missing_records():
    _clear_artifacts()
    resp = client.get("/artifacts/latest")
    assert resp.status_code == 200
    body = resp.json()
    assert body["playable_url"] is None
    assert body["version"] is None
