# Quickstart — Sketch Brawl Demo Delivery

## Prerequisites
- Node.js 20+, Yarn 4 (or pnpm) for `frontend/`
- Python 3.11 + Poetry for `backend/`
- Railway CLI logged in with access to project
- Docker (optional) for local container parity
- Redis 7 and PostgreSQL 15 reachable locally (Docker Compose provided later)

## 1. Clone + Install
```bash
git checkout 001-ai-game-demo
cd backend && poetry install && cd ..
cd frontend && yarn install && cd ..
```

## 2. Bootstrap Local Infra
```bash
# from repo root
cp ops/.env.example .env # contains API keys + Railway defaults
make dev-infra # docker compose up postgres, redis, minio
```

## 3. Run Backend
```bash
cd backend
poetry run alembic upgrade head
poetry run uvicorn src.api.main:app --reload --port 8000
```

## 4. Run Battle Worker + Telemetry Exporter
```bash
cd backend
poetry run celery -A src.workers.celery_app worker -l info
poetry run python -m src.workers.telemetry_export
```

## 5. Run Frontend Canvas
```bash
cd frontend
yarn dev --port 3000
```
Open http://localhost:3000, create invite link, open two browser windows, and draw.

## 6. Validate Constitution Gates
- **Input Fidelity**: run `yarn test:latency` (Playwright) to confirm <=50 ms strokes + >=60 fps.
- **AI Attribution**: call `/doodles` with sample payload and ensure `/doodles/{ticket}` returns within 1.5 s.
- **Deterministic Battles**: execute `poetry run pytest tests/integration/test_replay.py` to compare logs vs replays.
- **Skill Guardrails**: run `poetry run pytest tests/unit/test_validation.py` for max elements/attack.
- **Demo Readiness**: `make smoke-demo` builds frontend, runs scripted replay, and verifies Railway artifact links.

## 7. Package Demo Artifacts
```bash
make build-frontend # static files
make bundle-demo # zips logs + walkthrough video + spectator script
railway up --service frontend
railway up --service canvas-api
railway up --service battle-worker
```
Publish new artifact metadata via `/artifacts/latest` endpoint.
