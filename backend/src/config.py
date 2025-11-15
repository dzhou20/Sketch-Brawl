"""Application configuration and settings helpers (env-driven)."""
from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass
class Settings:
    app_name: str
    environment: str
    version: str
    database_url: str
    redis_url: str
    gemini_api_key: str | None
    gemini_model: str


def _load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Sketch Brawl API"),
        environment=os.getenv("ENVIRONMENT", "local"),
        version=os.getenv("APP_VERSION", "0.1.0"),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://brawl:brawl@localhost:5432/brawl",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
    )


@lru_cache
def get_settings() -> Settings:
    return _load_settings()
