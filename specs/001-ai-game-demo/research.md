# Phase 0 Research — Sketch Brawl Demo Delivery

## Decision: React + Fabric.js canvas for doodle capture
- **Rationale**: Fabric.js gives vector path access, supports pressure/velocity data, and plays well with React 18 + WebGL fallback. Performance benchmarks show <=5 ms per stroke processing on modern laptops, enabling the constitution's <=50 ms latency / >=60 fps target when combined with requestIdleCallback batching. Works in browsers judges already use; Unity canvas kept for replay only.
- **Alternatives Considered**:
  - **HTML5 Canvas 2D API directly**: Lowest dependency count but lacks built-in object model and would require more manual work for undo/redo, stroke serialization, and hit testing—which risks latency regressions.
  - **Unity WebGL front-end**: Strong rendering but slower startup (~10s) and heavier bundle; overkill for authoring doodles.

## Decision: Python FastAPI inference orchestrator using ONNX runtime
- **Rationale**: Python ecosystem already used for AI/ML; ONNX runtime loads custom CNN checkpoints exported from training notebooks. FastAPI provides async pipeline to fan out monster vs skill classification, apply deterministic seed injection, and finish within 1.5 s SLA. TorchServe alternative unnecessary; ONNX runtime loads faster on Railway limited memory.
- **Alternatives Considered**:
  - **C# minimal API + ML.NET**: Attractive for team skills but ML.NET image classification pipelines struggle with custom doodle semantics; limited ONNX operator support for style-transfer layers.
  - **External SaaS vision API**: Faster to start but little control over determinism or explanation text; also harder to ship offline recap pack.

## Decision: Deterministic battle engine as standalone Python module with Hypothesis tests
- **Rationale**: Implementing engine separately ensures RNG seeding, elemental reactions, and damage logs remain deterministic. Using dataclasses + numpy for calculations keeps code simple; Hypothesis property tests verify commutativity and log integrity. This aligns with constitution's Deterministic Auto-Battle Loop principle.
- **Alternatives Considered**:
  - **Running battle logic inside frontend**: Violates server-authoritative requirement and makes tampering detection hard.
  - **Embedding inside Postgres stored procedures**: Deterministic but hard to iterate, limited tooling for logging/replay exports.

## Decision: Railway deployment topology (3 services + object storage)
- **Rationale**: Railway can run multiple containers per project. Plan uses services: `canvas-api` (FastAPI + Postgres + Redis), `battle-worker` (Celery worker for battle/resync tasks), `frontend` (Next.js static build served via Railway). Demo video + replay archives stored in Railway's object storage plugin, synced nightly to offline bundle. Railway's auto SSL and secret management simplifies gating; monitors satisfy Demo-Ready Delivery checks.
- **Alternatives Considered**:
  - **Vercel + Railway hybrid**: Splitting frontend/back adds cross-cloud latency and complicates environment variables.
  - **Self-hosted VPS**: More control but slower to provision and lacks one-click rollbacks; harder to show maintainability to judges.

## Decision: Telemetry + replay export pipeline via PostgreSQL JSONB + S3-compatible bucket
- **Rationale**: Using JSONB columns for telemetry events allows flexible shaping of canvas latency samples, inference durations, and battle logs. Nightly job exports aggregated stats + zipped logs to S3-compatible object storage, enabling offline recap pack. Keeps instrumentation centralized and queryable for dashboards.
- **Alternatives Considered**:
  - **Timeseries DB (Influx/Prometheus)**: Great for metrics but extra infra overhead for hackathon timeline.
  - **Plain log files**: Harder to join with player sessions and does not provide structured evidence for constitution checks.
