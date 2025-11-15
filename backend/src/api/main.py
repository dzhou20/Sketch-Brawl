"""FastAPI entrypoint for Sketch Brawl backend."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from src.api import doodles, lobbies, telemetry
from src.config import get_settings
from src.infra.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    # Hook for DB/Redis connection pools and telemetry wiring
    yield


app = FastAPI(title="Sketch Brawl", lifespan=lifespan)
app.include_router(lobbies.router, prefix="/lobbies", tags=["lobbies"])
app.include_router(doodles.router, prefix="/doodles", tags=["doodles"])
app.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])


@app.get("/health", tags=["ops"])
async def read_health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "version": settings.version, "env": settings.environment}
