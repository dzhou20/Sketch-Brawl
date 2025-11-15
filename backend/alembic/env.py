from logging.config import fileConfig
from pathlib import Path
import sys

from sqlmodel import SQLModel
from alembic import context

# Ensure backend/src is on path so imports work when running from backend root
ROOT = Path(__file__).resolve().parents[1]  # backend/alembic -> backend
SRC = ROOT / "src"
for path in [ROOT, SRC]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from api.main import get_settings  # type: ignore  # noqa: E402
from infra.database import get_engine  # type: ignore  # noqa: E402
import models  # type: ignore  # noqa: E402,F401 ensures models imported

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    url = get_settings().database_url
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


def run_migrations() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


run_migrations()
