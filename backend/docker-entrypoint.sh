#!/bin/bash
set -euo pipefail

WAIT_SECONDS=${DB_WAIT_SECONDS:-30}
RETRY_DELAY=${DB_RETRY_DELAY:-1}

echo "[entrypoint] waiting for database..."
python - <<'PY'
import os
import sys
import time
from sqlalchemy import create_engine, text

wait_seconds = int(os.environ.get("DB_WAIT_SECONDS", "30"))
retry_delay = float(os.environ.get("DB_RETRY_DELAY", "1"))
database_url = os.environ.get("DATABASE_URL")

if not database_url:
    print("DATABASE_URL is not set", file=sys.stderr)
    sys.exit(1)

engine = create_engine(database_url)
deadline = time.time() + wait_seconds

while True:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        break
    except Exception as exc:  # pragma: no cover - startup only
        if time.time() > deadline:
            print(f"Database not ready: {exc}", file=sys.stderr)
            sys.exit(1)
        time.sleep(retry_delay)
PY

echo "[entrypoint] running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] starting uvicorn..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
