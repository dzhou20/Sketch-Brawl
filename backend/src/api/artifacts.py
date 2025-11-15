"""Demo artifact API endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from src.services.artifact_service import ArtifactService

router = APIRouter()
service = ArtifactService()


class ArtifactResponse(BaseModel):
  playable_url: str | None = None
  walkthrough_video_url: str | None = None
  offline_bundle_url: str | None = None
  version: str | None = None


@router.get("/latest", response_model=ArtifactResponse)
async def get_latest_artifacts() -> ArtifactResponse:
    payload = service.get_latest()
    return ArtifactResponse(**payload)
