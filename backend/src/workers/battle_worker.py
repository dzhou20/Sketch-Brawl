"""Celery worker to process battle jobs asynchronously."""
from __future__ import annotations

import os

from celery import Celery

from src.services.battle_service import BattleService

CELERY_BROKER = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER)

celery_app = Celery("battle_worker", broker=CELERY_BROKER, backend=CELERY_BACKEND)
battle_service = BattleService()


@celery_app.task(name="battle.run_hotseat")
def run_battle_task(lobby_id: str, seed: int | None = None) -> dict:
    """Execute a single battle for the specified lobby."""
    return battle_service.start_battle(lobby_id, seed)
