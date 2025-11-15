# Implementation Plan: Sketch Brawl Demo Delivery

**Branch**: `001-ai-game-demo` | **Date**: 2025-11-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-game-demo/spec.md`

## Summary

Build a submission-ready Sketch Brawl demo where two players sketch monsters/skills,
AI assigns combat attributes, and a deterministic server resolves battles with replay
logs plus guided demo assets. Delivery includes: low-latency doodle canvas, AI
attribution flow with explanations, server-authoritative battle simulator, upgrade
validation, telemetry dashboards, Railway deployment, and packaged demo artifacts.

## Technical Context

**Language/Version**: Python 3.11 (backend services, telemetry workers); TypeScript 5 + React 18 (web canvas + UI); Unity WebGL (optional guided replay viewer embedded as iframe)  
**Primary Dependencies**: FastAPI, PostgreSQL 15, Redis 7, PlayCanvas-like WebGL canvas or Fabric.js for drawing, TorchServe/ONNX runtime for image-to-attribute inference, Railway deployment stack  
**Storage**: PostgreSQL for Monsters/SkillCards/BattleSessions, Redis for lobby presence + deterministic seed queue, object storage (Railway plugin) for demo artifacts/log bundles  
**Testing**: Pytest + Hypothesis for battle math, Playwright for frontend canvas/inference loop, Locust scripts for latency soak tests  
**Target Platform**: Desktop browsers (Chrome/Edge) at 1920x1080 with fallback 1280x720; backend hosted on Railway containers  
**Project Type**: Web frontend + backend services  
**Performance Goals**: <=50 ms canvas latency, >=60 fps rendering, <=1.5 s AI inference P95, <=10 s battle resolution P95, Railway cold start <=5 s  
**Constraints**: Deterministic RNG seed propagation, bilingual UI copy, offline replay exports, invite-link access only, Railway resource quotas (2 vCPU/2 GB per service)  
**Scale/Scope**: Two concurrent human players + judge spectators per lobby during demos; telemetry sized for 50 recorded sessions and 10 guided replays

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Input Fidelity**: Plan includes canvas instrumentation (PerformanceObserver + worker) and Redis-backed telemetry to ensure <=50 ms latency, >=60 fps with pre-round pause if breached.
- **AI Attribution Transparency**: FastAPI inference gateway enforces <=1.5 s SLA, stores prompt + seed + explanation JSON per doodle, and exposes UI overlays + judge logs.
- **Deterministic Battles**: Python battle engine consumes persisted Monster/SkillCard data + single RNG seed, logs every damage event, and exports replay JSON for playback.
- **Skill Evolution Guardrails**: Validation service enforces max three elements, additive attack caps, cooldown rules, and annotates failures so UI can block upgrades.
- **Demo Readiness**: CI publishes Railway-hosted build + <=90 s walkthrough video, spectate scripts, and offline recap packs; smoke test checklist runs after each merge.

_All gates satisfied: requirements mapped to specific components and metrics with telemetry + CI evidence. No violations to justify._

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-game-demo/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/             # FastAPI routers (lobby, doodle upload, battles, telemetry)
│   ├── services/        # AI attribution, battle engine, upgrade validator
│   ├── models/          # SQLModel entities + seed persistence
│   ├── workers/         # Replay exporter, telemetry aggregator
│   └── infra/           # Railway config, Redis/Postgres clients
└── tests/
    ├── unit/
    ├── integration/
    └── load/

frontend/
├── src/
│   ├── components/      # Canvas, AI explanation panel, battle HUD, tutorial overlays
│   ├── pages/           # Lobby, Match, Guided Replay, Admin smoke test
│   ├── services/        # API clients, telemetry publisher
│   └── store/           # Deterministic state synced with server seed
└── tests/
    ├── e2e/             # Playwright
    └── visual/

unity-guided/
└── Assets/              # Optional WebGL replay visualizer packaged for iframe use
```

**Structure Decision**: Dual repo folders (`backend`, `frontend`) enable independent deployments + Railway services; Unity WebGL assets remain optional add-on referenced by frontend.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Second runtime (Unity WebGL) | Enables cinematic guided replay judges expect | Plain React animation cannot show 3D doodle transformations convincingly |
| Redis cache | Required for lobby presence + deterministic seed queue | Postgres alone cannot guarantee low-latency presence updates |

## Constitution Re-evaluation (Post Phase 1)

- **Input Fidelity**: research.md + quickstart cover Fabric.js instrumentation, telemetry event schema, and Playwright latency tests—no gaps.
- **AI Attribution**: data-model + contracts define ONNX-backed inference endpoints with persisted prompts/seeds; SLA documented in quickstart step 6.
- **Deterministic Battles**: data-model describes RNG + replay logs; contracts expose `/battles/{id}/replay`; research details Hypothesis test plan.
- **Skill Evolution Guardrails**: SkillCard validations + `/skills/{id}/reinforce` endpoint enforce stacking rules and error reporting.
- **Demo Readiness**: quickstart + DemoArtifact entity + `/artifacts/latest` endpoint ensure Railway deployment + offline bundle steps captured.
