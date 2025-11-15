"""Database session helpers."""
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from src.config import get_settings

_engine = create_engine(get_settings().database_url, echo=False, future=True)


def get_engine():
    return _engine


def init_db() -> None:
    SQLModel.metadata.create_all(_engine)


def get_session() -> Generator[Session, None, None]:
    with Session(_engine) as session:
        yield session
