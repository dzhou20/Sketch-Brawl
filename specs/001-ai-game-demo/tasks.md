---

description: "Updated task list for Sketch Brawl demo implementation"

---

# Tasks: Sketch Brawl Demo Delivery

**Input**: Design documents from `/specs/001-ai-game-demo/`  
**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Constitution gates demand latency, inference, and determinism evidence, so each story keeps explicit validation tasks. Only add other tests if they help prove those gates.

**Organization**: Tasks stay grouped by user story to keep each increment independently testable and demoable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Different files + no dependencies ⇒ safe to parallelize
- **[Story]**: `[US1]`, `[US2]`, `[US3]` for story-scoped tasks. Setup/Foundational/Polish omit the story tag.
- Always include an exact file path in the description.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repo scaffolding + dev infra so backend/frontend share the same toolchain.

- [X] T001 Scaffold backend Poetry project with FastAPI + SQLModel deps in `backend/pyproject.toml`
- [X] T002 Create FastAPI entrypoint + settings loader in `backend/src/api/main.py`
- [X] T003 Initialize Next.js + TypeScript workspace with lint/test scripts in `frontend/package.json`
- [X] T004 Provision dev docker-compose with Postgres, Redis, MinIO in `ops/docker-compose.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared data models, persistence, telemetry, and inference plumbing required before any story work.

- [X] T005 Define Monster & SkillCard SQLModel entities (seed, snapshot slots) in `backend/src/models/monster.py`
- [X] T006 Add BattleSession, TelemetryEvent, DemoArtifact models + JSON timelines in `backend/src/models/battle_session.py`
- [X] T007 Configure database session + Alembic migrations in `backend/alembic/`
- [X] T008 Implement ONNX/Gemini inference runner with deterministic seed injection in `backend/src/services/inference_runner.py`
- [X] T009 Build telemetry ingestion service backed by Redis Streams in `backend/src/services/telemetry.py`
- [X] T010 Establish typed API client + deterministic lobby store in `frontend/src/services/apiClient.ts` and `frontend/src/store/sessionStore.ts`

**Checkpoint**: Foundation complete → user stories can proceed independently.

---

## Phase 3: User Story 1 – Draw-to-Attribute Loop (Priority: P1) 🎯 MVP

**Goal**: Players draw monsters/skills, get AI-attributed stats + explanations within SLA, and see validation feedback before battles.

**Independent Test**: Dual-browser Playwright scenario draws a monster + skill, verifies <=50 ms canvas latency and >=60 fps, receives inference payload within 1.5 s, and finds Monster/SkillCard persisted with prompt + snapshot metadata.

### Tests for User Story 1 ⚠️

- [X] T011 [P] [US1] Add Playwright latency/FPS probe in `frontend/tests/e2e/draw-latency.spec.ts`
- [X] T012 [P] [US1] Create integration test for `/doodles` attribution + prompt persistence in `backend/tests/integration/test_inference.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement lobby/invite REST endpoints + Redis presence heartbeat in `backend/src/api/lobbies.py`
- [X] T014 [P] [US1] Build lobby service (invite validation, readiness state) in `backend/src/services/lobby_service.py`
- [X] T015 [US1] Implement Fabric.js-based DoodleCanvas with telemetry hooks and snapshot capture in `frontend/src/components/DoodleCanvas.tsx`
- [X] T016 [P] [US1] Create AI attribution panel + explanation UI in `frontend/src/components/AttributionPanel.tsx`
- [X] T017 [US1] Implement doodle upload + ticket retrieval endpoints in `backend/src/api/doodles.py`
- [X] T018 [P] [US1] Implement reinforcement validation rules in `backend/src/services/validation.py`
- [X] T019 [US1] Persist Monster/SkillCard records, seeds, and snapshot_data in `backend/src/services/attribute_store.py`
- [X] T020 [US1] Wire telemetry publisher (latency/fps/inference events) in `frontend/src/services/telemetryPublisher.ts`

**Checkpoint**: US1 end-to-end loop demoable on its own.

---

## Phase 4: User Story 2 – Hot-seat Auto Battles (Priority: P2)

**Goal**: On one device, Player A/B reuse their US1 monsters/skills, optionally reinforce skills, and launch deterministic best-of-three battles. UI must match `doc/AI-game` mock (timeline+summary) with no replay downloads.

**Independent Test**: Single-machine flow — Player A draws monster/skill, Player B draws monster/skill, host starts battle. Assert `/battles` POST log equals HUD timeline, POST/GET responses match, and Celery/SSE stream emits identical events for identical RNG seeds.

### Tests for User Story 2 ⚠️

- [ ] T021 [P] [US2] Expand Hypothesis property tests to cover multi-round summaries + reinforcement buffers in `backend/tests/unit/test_battle_engine.py`
- [X] T022 [P] [US2] Add integration test ensuring `/battles` POST vs GET timelines stay in sync in `backend/tests/integration/test_battle_api.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement deterministic battle engine (elements, rounds, logs) in `backend/src/services/battle_engine.py`
- [X] T024 [US2] Persist battle timeline + per-round summaries in `backend/src/services/battle_timeline.py`
- [X] T025 [US2] Extend AttributeStore to link Monster snapshots + Skill history entries in `backend/src/services/attribute_store.py`
- [X] T026 [US2] Compose BattleService to hydrate combatants + wins in `backend/src/services/battle_service.py`
- [X] T027 [US2] Provide `/battles` POST/GET endpoints with typed payloads in `backend/src/api/battles.py`
- [X] T028 [US2] Wire Celery worker `backend/src/workers/battle_worker.py` into `/battles` so hot-seat battles can run async and return job IDs
- [X] T029 [US2] Expose SSE/polling endpoint for live battle events in `backend/src/api/battles.py` and add client hook `frontend/src/hooks/useBattleStream.ts`
- [X] T030 [US2] Apply reinforcement history deltas to combat stats before simulations in `backend/src/services/battle_service.py`
- [X] T031 [US2] Add reinforcement selection & history UI (skill picker, upgrade log) in `frontend/src/pages/match.tsx` + `frontend/src/components/SkillHistoryPanel.tsx`
- [X] T032 [US2] Animate BattleHud events + judge summary overlays per `doc/AI-game` in `frontend/src/components/BattleHud.tsx`
- [X] T033 [US2] Document hot-seat workflow + skill reuse instructions in `specs/001-ai-game-demo/quickstart.md`
- [X] T046 [US2] Implement "AI thinking" overlay + submission confirmation states in `frontend/src/pages/match.tsx` and related components to match the Junction workflow (monster/gear draws)
- [X] T047 [US2] Add post-battle summary modal with "ready to fight" and "back to main menu" actions plus recap copy in `frontend/src/components/BattleHud.tsx`
- [X] T048 [US2] Provide guided gear/upgrade step indicators and contextual copy ("Draw your gear", "Upgrade your gear") in `frontend/src/pages/match.tsx` so each phase mirrors the storyboard

**Checkpoint**: US1 + US2 together provide the full hot-seat battle loop with deterministic evidence.

---

## Phase 5: User Story 3 – Demo Packaging & Frontend Handoff (Priority: P3)

**Goal**: Ship a Railway-hosted build + ≤90 s walkthrough video, bilingual tutorial overlays, and offline recap bundles for judges.

**Independent Test**: Run `make smoke-demo` to deploy preview, walk through bilingual tutorial, embed Unity replay iframe, and confirm `/artifacts/latest` returns playable/video/offline links.

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement Railway smoke-test script + CI hook in `ops/scripts/smoke_demo.ts`
- [X] T035 [US3] Build bilingual tutorial + judge checklist page in `frontend/src/pages/tutorial.tsx`
- [ ] T036 [P] [US3] Integrate Unity WebGL guided replay iframe + captions in `frontend/src/pages/guided-replay.tsx`
- [ ] T037 [US3] Configure CI workflow to build/upload demo artifacts in `ops/ci/demo-artifacts.yml`
- [ ] T038 [P] [US3] Implement offline recap bundler (logs + video + instructions) in `ops/scripts/bundle_demo.py`
- [X] T039 [US3] Expose `/artifacts/latest` API returning playable/video/offline URIs in `backend/src/api/artifacts.py`
- [ ] T040 [US3] Document judge walkthrough + embed links in `docs/judge-walkthrough.md`
- [ ] T041 [US3] Localize critical UI copy (zh-CN + en-US) in `frontend/src/i18n/demo.json`

**Checkpoint**: Hosted demo, tutorial, and artifact delivery meet submission requirements.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Hardening + documentation across stories.

- [ ] T042 [P] Harden telemetry dashboards + constitution evidence write-up in `docs/telemetry.md`
- [ ] T043 Execute load tests for inference/battle services using Locust in `backend/tests/load/locustfile.py`
- [ ] T044 [P] Add Railway observability/alert rules (uptime, SLA) in `ops/monitoring/railway-alerts.yml`
- [ ] T045 Final QA pass updating `specs/001-ai-game-demo/quickstart.md` + smoke checklist after demo polishing

---

## Dependencies & Execution Order

- **Phase 1 → Phase 2**: Setup unblocks foundational infra.
- **Phase 2 → US1/US2/US3**: All user stories depend on completed models, inference, and telemetry.
- **US1 → US2**: US2 reuses US1 monsters/skills and telemetry; US1 must be green before expanding battles.
- **US2 → US3**: Packaging tasks rely on hot-seat gameplay being stable.
- **Polish**: Runs after target user stories are feature-complete.

---

## Parallel Execution Examples

- **US1**: While `frontend/src/components/DoodleCanvas.tsx` (T015) evolves, another dev can implement `backend/src/api/doodles.py` (T017) since both rely on the validated schema but touch different stacks.
- **US2**: Timeline persistence (T024) and HUD animation (T032) can progress concurrently once the contract (`BattleResponse`) is defined; SSE plumbing (T029) should follow Celery integration (T028) but can run parallel to reinforcement UI (T031).
- **US3**: CI workflow work (T037) and offline bundle tooling (T038) touch different folders, so they can run simultaneously while the tutorial page (T035) is being built.

---

## Implementation Strategy

1. **MVP (US1)**: Already complete—keep telemetry probes and inference stability monitored.
2. **Extend to Hot-seat Battles (US2)**: Finish Celery/SSE, reinforcement math/UI, and quickstart docs so the on-device PvP experience is deterministic and traceable.
3. **Demo Packaging (US3)**: Once gameplay is stable, focus on Railway smoke tests, tutorials, localization, and artifact publishing.
4. **Polish**: Run load tests, finalize telemetry evidence, and update quickstart before submission.

Suggested MVP scope for rapid demos remains **US1**, but US2 adds the differentiating battle experience needed for the final submission.
