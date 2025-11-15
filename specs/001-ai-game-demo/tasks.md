---

description: "Task list for Sketch Brawl demo implementation"
---

# Tasks: Sketch Brawl Demo Delivery

**Input**: Design documents from `/specs/001-ai-game-demo/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Constitution gates require telemetry + replay evidence, so each story includes mandatory validation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization that wires the fast sketch canvas stack, FastAPI backend, and Railway-ready infra.

- [ ] T001 Scaffold backend Poetry project with FastAPI/SQLModel deps in `backend/pyproject.toml`
- [ ] T002 Create FastAPI entrypoint + settings loader in `backend/src/api/main.py`
- [ ] T003 Initialize Next.js + TypeScript workspace with lint/test scripts in `frontend/package.json`
- [ ] T004 Provision dev docker-compose with Postgres, Redis, MinIO in `ops/docker-compose.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure (data models, persistence, telemetry, inference runtime) that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Define Monster & SkillCard SQLModel entities + seed columns in `backend/src/models/monster.py` and `backend/src/models/skill_card.py`
- [ ] T006 Add BattleSession, TelemetryEvent, DemoArtifact models + relationships in `backend/src/models/battle_session.py`
- [ ] T007 Configure database session + Alembic migration scripts in `backend/alembic/`
- [ ] T008 Implement ONNX inference runner scaffold with deterministic seed injection in `backend/src/services/inference_runner.py`
- [ ] T009 Build telemetry ingestion/aggregation service with Redis queue fan-out in `backend/src/services/telemetry.py`
- [ ] T010 Establish typed API client + deterministic state store in `frontend/src/services/apiClient.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Draw-to-Attribute Loop (Priority: P1) 🎯 MVP

**Goal**: Players draw monsters/skills, receive AI-attributed stats + explanations within SLA, and see validation feedback before battles.

**Independent Test**: Run dual-browser Playwright scenario that draws a monster + skill, verifies <=50 ms latency metrics, receives inference payload within 1.5 s, and confirms persisted attributes in DB.

### Tests for User Story 1 ⚠️

- [ ] T011 [P] [US1] Add Playwright canvas latency + FPS probe in `frontend/tests/e2e/draw-latency.spec.ts`
- [ ] T012 [P] [US1] Create backend integration test for `/doodles` attribution + prompt persistence in `backend/tests/integration/test_inference.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement lobby/invite REST endpoints + Redis presence heartbeat in `backend/src/api/lobbies.py`
- [ ] T014 [P] [US1] Build lobby service (invite validation, readiness state) in `backend/src/services/lobby_service.py`
- [ ] T015 [US1] Implement Fabric.js-based DoodleCanvas with telemetry hooks in `frontend/src/components/DoodleCanvas.tsx`
- [ ] T016 [P] [US1] Create AI attribution panel + explanation UI in `frontend/src/components/AttributionPanel.tsx`
- [ ] T017 [US1] Implement doodle upload + inference ticket API in `backend/src/api/doodles.py`
- [ ] T018 [P] [US1] Implement reinforcement validation rules + error payloads in `backend/src/services/validation.py`
- [ ] T019 [US1] Persist Monster/SkillCard records + seeds after inference in `backend/src/services/attribute_store.py`
- [ ] T020 [US1] Wire telemetry publisher (latency/fps/inference events) in `frontend/src/services/telemetryPublisher.ts`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Server-Authoritative Auto Battles (Priority: P2)

**Goal**: Run deterministic best-of-three auto battles, stream events to clients, store replay logs, and expose download endpoints.

**Independent Test**: Trigger battle via API using stored monsters/skills and verify Hypothesis + integration tests prove damage logs equal replay playback.

### Tests for User Story 2 ⚠️

- [ ] T021 [P] [US2] Write Hypothesis property tests for battle math determinism in `backend/tests/unit/test_battle_engine.py`
- [ ] T022 [P] [US2] Add replay consistency integration test covering `/battles/{id}/replay` in `backend/tests/integration/test_replay_consistency.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement deterministic battle engine (damage, elements, timers) in `backend/src/services/battle_engine.py`
- [ ] T024 [US2] Create Celery worker to run rounds + enforce RNG seeds in `backend/src/workers/battle_worker.py`
- [ ] T025 [US2] Add battle API (start battle, SSE updates, replay fetch) in `backend/src/api/battles.py`
- [ ] T026 [US2] Build battle HUD + log viewer in `frontend/src/components/BattleHud.tsx`
- [ ] T027 [P] [US2] Implement replay playback UI + download button in `frontend/src/pages/match.tsx`
- [ ] T028 [US2] Export replay JSON with checksum + storage upload in `backend/src/services/replay_exporter.py`
- [ ] T029 [US2] Record skill evolution deltas + history for upgrades in `backend/src/services/skill_history.py`

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Demo Packaging & Frontend Handoff (Priority: P3)

**Goal**: Provide Railway deployment, guided replay/tour, bilingual instructions, and offline recap packs for judges.

**Independent Test**: Run `make smoke-demo` to deploy to Railway preview, execute guided replay walkthrough, verify bilingual UI, and confirm build link + video metadata exposed via `/artifacts/latest`.

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement Railway smoke-test script + CI hook in `ops/scripts/smoke_demo.ts`
- [ ] T031 [US3] Build bilingual tutorial + judge checklist page in `frontend/src/pages/tutorial.tsx`
- [ ] T032 [P] [US3] Integrate Unity WebGL guided replay iframe + captions in `frontend/src/pages/guided-replay.tsx`
- [ ] T033 [US3] Configure CI workflow to build/upload demo artifacts to Railway storage in `ops/ci/demo-artifacts.yml`
- [ ] T034 [P] [US3] Implement offline recap bundler (logs + video + instructions) in `ops/scripts/bundle_demo.py`
- [ ] T035 [US3] Expose `/artifacts/latest` API returning playable/video/offline URIs in `backend/src/api/artifacts.py`
- [ ] T036 [US3] Document judge walkthrough + embed links in `docs/judge-walkthrough.md`
- [ ] T037 [US3] Localize critical UI copy (zh-CN + en-US) in `frontend/src/i18n/demo.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Wrap-up work covering documentation, performance, and validation across stories

- [ ] T038 [P] Harden telemetry dashboards + docs describing evidence capture in `docs/telemetry.md`
- [ ] T039 Execute load tests for inference/battle services using Locust in `backend/tests/load/locustfile.py`
- [ ] T040 [P] Add observability/alert rules for Railway (uptime, SLA) in `ops/monitoring/railway-alerts.yml`
- [ ] T041 Final QA pass updating quickstart + smoke checklist in `specs/001-ai-game-demo/quickstart.md`

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → initializes repos/infrastructure
- **Foundational (Phase 2)** → depends on Setup; blocks US1, US2, US3
- **US1** → starts after Foundational; outputs canvas + attribution loop for MVP
- **US2** → depends on US1 data structures (monsters/skills) but battle logic otherwise independent
- **US3** → depends on US1+US2 for demo content; handles packaging + hosting
- **Polish** → final hardening after selected stories complete

## Parallel Opportunities

- During Setup, backend and frontend scaffolding (T001 vs T003) can run concurrently
- In US1, lobby service (T014) and attribution panel (T016) can progress in parallel once API contracts ready
- US2 replay UI (T027) can proceed while backend worker (T024) finalizes since it consumes mocked logs
- US3 tutorial page (T031) and CI artifacts workflow (T033) operate independently until final verification

## Implementation Strategy

1. Complete Phases 1-2 to guarantee stable infra, telemetry, and inference backbone.
2. Deliver US1 as MVP: canvas draw, AI attribution, validation, telemetry proof.
3. Layer in US2 deterministic battles + replay export to showcase gameplay depth.
4. Finish with US3 demo packaging so judges have hosted build, guided replay, and bilingual copy.
5. Run Polish tasks to validate performance, documentation, and monitoring before submission.
