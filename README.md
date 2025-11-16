# Sketch-Brawl

Sketch Brawl is an AI-powered doodle battler where anything you draw becomes alive — and fights.
Players sketch monsters and gear like a kid, and the AI instantly interprets each stroke into stats, abilities,
personalities, and chaotic battle actions. Every match is unpredictable, creative, and powered entirely by your
imagination.
![Banner](https://github.com/dzhou20/Sketch-Brawl/blob/001-ai-game-demo/doc/Sketch-Brawl-Logo-Rect.png)

---

## Toolbox by Layer

### Backend stack (FastAPI + SQLModel)

1. Start the PostgreSQL, Redis, MinIO, and FastAPI services via Compose:
   ```bash
   docker compose -f ops/docker-compose.yml up --build postgres redis minio backend
   ```
2. When the stack is healthy the FastAPI backend listens on `http://localhost:8000`.

#### Required environment

Set the Gemini key (or other inference API credentials) before launching the backend:

```bash
export GEMINI_API_KEY=<your-key>
```

You can drop the same variable into `/.env` for easier re-use.

### Frontend (Next.js + React)

1. Enter the frontend workspace:
   ```bash
   cd frontend
   ```
2. Install dependencies, then boot the dev server:
   ```bash
   yarn install
   yarn dev --hostname 127.0.0.1 --port 3000
   ```

The Next.js app runs at `http://127.0.0.1:3000` and proxies API calls through `pages/api/proxy`.

---

## Helpful Commands

- `docker compose -f ops/docker-compose.yml up --build`: builds + launches all backend dependencies.
- `docker compose -f ops/docker-compose.yml down`: stops containers.
- `cd frontend && yarn lint`: runs the Next lint suite (currently fails until ESLint CLI flags are updated).
- `cd frontend && yarn dev`: starts the UI with hot reload.
- `cd backend && poetry run pytest`: exercises Python services and API contracts.

## UI previews

![Banner](https://github.com/dzhou20/Sketch-Brawl/blob/001-ai-game-demo/doc/ui.png)
## Diagram

```
[Browser / Next.js UI]
    ↓
[pages/api/proxy] ───► [FastAPI backend]
                          ├─► Battle engine / timeline builder
                          ├─► Inference runner (TorchServe / Gemini)
                          └─► Persists to PostgreSQL / Redis / MinIO
```

## Folder structure

- `backend/`: FastAPI services, SQLModel models, inference runner, telemetry, and battle logic.
- `frontend/`: Next.js + React UI, DoodleCanvas, Battle HUD, BattleStage, API proxy, and Zustand store.
- `ops/`: Docker compose setup for Postgres, Redis, MinIO, and backend.
- `specs/001-ai-game-demo/`: Research, plan, spec, quickstart, and tasks for the ai-game demo.
- `doc/`: Supporting documentation and UI mock assets (UI.jpeg, spec diagrams).
