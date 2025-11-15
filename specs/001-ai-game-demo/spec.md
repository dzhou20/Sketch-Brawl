# Feature Specification: Sketch Brawl Demo Delivery

**Feature Branch**: `001-ai-game-demo`  
**Created**: 2025-11-15  
**Status**: Draft  
**Input**: User description: "帮我打造这个AI游戏demo，保证提到的功能都能实现，并与前端UI良好交互"

## User Scenarios & Testing *(mandatory)*

Each story MUST call out which constitution principles it satisfies (input fidelity,
AI transparency, deterministic battle loop, skill evolution guardrails, demo readiness)
and document the metric or artifact (latency budget, replay log, build link, video) that
proves compliance.

### User Story 1 - Draw-to-Attribute Loop (Priority: P1)

Two remote players join a lobby, draw their monster and first skill on the shared canvas, and immediately see the AI-interpreted attributes plus rationale before the battle starts.

**Principles & Evidence**: Input Fidelity (stroke latency logs <=50 ms, >=60 fps dashboards), Transparent AI Attribution (1.5 s inference SLA with prompt + seed persisted).  
**Why this priority**: Without trustworthy draw-to-attribute translation, no subsequent gameplay or judging is possible.  
**Independent Test**: Run a 2-player session capturing latency telemetry and verifying the AI summary panel to validate inputs, even if auto-battle is stubbed out.

**Acceptance Scenarios**:

1. **Given** both players are on the lobby canvas, **When** they finish drawing a monster, **Then** the UI displays the interpreted element, HP, attack, and explanation text within 1.5 seconds and persists the seed/prompts for replay.
2. **Given** a player draws a reinforcement skill doodle, **When** the AI detects a validation violation (e.g., >3 elements), **Then** the UI blocks the submission and highlights the exact stacking rule breached.

---

### User Story 2 - Hot-seat Auto Battles (Priority: P2)

On a single device, Player A and Player B take turns drawing monsters/skills (via US1 flow), then launch a best-of-three server-authoritative battle; the UI streams events and renders round summaries per the `doc/AI-game` mock so judges can verify the outcome on the same screen with no downloads.

**Principles & Evidence**: Deterministic Auto-Battle Loop (server log mirrors UI timeline), Skill Evolution Guardrails (upgrade deltas recorded), Demo Readiness (spectator HUD referencing live events).  
**Why this priority**: Judges need to see a full PvP-looking loop even without networking; hot-seat makes it shippable for the demo while still proving determinism.  
**Independent Test**: Run the full hot-seat flow locally: Player A draws → Player B draws → battle runs. Assert the battle log emitted by the API matches the UI timeline for identical seeds and that both players’ Monster/SkillCard records from US1 are reused without re-inference.

**Acceptance Scenarios**:

1. **Given** both player slots have saved monsters/skills, **When** the host device starts a round, **Then** the server simulates damage using the RNG seed, streams events to the same client, and logs each hit/KO so the on-screen timeline (matching `doc/AI-game`) reflects the authoritative source.
2. **Given** a round finishes, **When** the judge expands the inline summary, **Then** the UI shows the same KO order, damage totals, and overtime flags recorded by the server log, proving determinism without needing replay downloads.

---

### User Story 3 - Demo Packaging & Frontend Handoff (Priority: P3)

Deliver a playable link plus ≤90 second walkthrough video that demonstrates the full loop (draw, AI explain, battle, upgrades) with bilingual-ready UI copy and guidance overlays for the judging panel.

**Principles & Evidence**: Demo-Ready Delivery (hosted build link uptime checks, scripted video), Input Fidelity & AI Transparency (UI overlays referencing telemetry).  
**Why this priority**: Submission success for the AI hackathon depends on a polished experience and clear instructions for evaluators.  
**Independent Test**: Run the smoke-test checklist that loads the hosted build in a fresh browser, walks through matchmaking, records the guided video script, and confirms all instructions render correctly in Chinese + English placeholders.

**Acceptance Scenarios**:

1. **Given** a new judge opens the playable link, **When** they follow the on-screen bilingual tutorial, **Then** they can watch a guided battle replay end-to-end without needing external documentation.
2. **Given** the feature is merged to main, **When** the CI job publishes artifacts, **Then** the hosted demo link and the prerecorded ≤90 second walkthrough video are updated and referenced from the submission tracker.

---

### Edge Cases

- AI inference exceeds 1.5 seconds, conflicts with canvas inputs, or times out mid-round; the UI must surface fallback stats or allow redraw before battle.
- Canvas telemetry detects >50 ms latency or dropped strokes on one player—system pauses round start and prompts to recalibrate before unfair play occurs.
- Upgrade validation rejects stacked effects due to element count, additive attack caps, or cooldown tampering; history audit trail must show which doodle caused the block.
- Battle replay diverges from authoritative logs during demo capture; submissions halt with actionable error messaging and instructions to regenerate.
- Playable build link or demo video becomes unavailable pre-submission; automation must alert owners and provide cached offline “guided battle” assets.
- Remote players desync (network loss, late join) while front-end UI expects synchronous input; lobby must handle reconnect or switch to AI placeholder opponent without corrupting logs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture doodle strokes at <=50 ms latency and >=60 fps with telemetry proving compliance.
- **FR-002**: AI attribution MUST complete within 1.5 seconds, store prompts + seeds, and output explanation text shown to both players and judges.
- **FR-003**: Auto-battle resolution MUST run server-side from persisted attributes + single RNG seed and produce a replay log for each damage event.
- **FR-004**: Skill upgrades MUST enforce stacking rules (max three elements, additive attack caps, cooldown changes logged) and block invalid submissions with clear errors.
- **FR-005**: Build delivery MUST include a live playable link + <=90 second walkthrough video script that is smoke-tested after each merge.
- **FR-006**: Lobby MUST allow two human players or one human + AI bot to join via shareable invite URL, showing readiness state before canvases unlock.
- **FR-007**: Frontend MUST expose bilingual-ready UI copy for every judge-facing instruction, including drawing guidance, AI explanation, battle log legend, and tutorial overlays.
- **FR-008**: Telemetry dashboard MUST aggregate latency, inference time, battle duration, win/loss, and validation failures per session, exportable for the submission recap.
- **FR-009**: Spectate/guided battle mode MUST let judges replay a curated match with scripted captions even if live opponents are unavailable.
- **FR-010**: Offline recap pack MUST bundle replay logs, prompts/seeds, and demo video so judges can verify functionality without network access.

*Example of marking unclear requirements:*

- **FR-011**: Lobby access MUST rely on private invite links without additional authentication; following a link grants a temporary anonymous slot for the demo session.
- **FR-012**: Playable build and backend services MUST be deployed via Railway-managed environments, with fallback guidance if the chosen tech stack requires complementary hosting for static assets or video storage.

### Key Entities *(include if feature involves data)*

- **Monster**: Canonical representation of a player's doodled creature. Attributes include name, HP, base attack, element, seed, owning player ID, and AI explanation; immutable per battle.
- **SkillCard**: Weapon/defense/augment doodle tied to a monster. Stores stacked elements, additive attack bonuses, cooldown adjustments, and ordered reinforcement history for auditing.
- **BattleSession**: Server-authoritative record containing participating player IDs, RNG seed, ordered damage events, overtime markers, and replay export pointers for each round in best-of-three play.
- **TelemetryEvent**: Structured log entry covering canvas latency, inference durations, validation rejections, battle runtime, or demo artifact status; feeds dashboards and submission summaries.
- **DemoArtifact**: Versioned pointer to hosted playable build, guided battle script, and ≤90 second walkthrough video ensuring hackathon submission readiness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of doodle sessions maintain <=50 ms latency and >=60 fps over 5-minute tests on target hackathon laptops, with alerts triggered for any sustained violation.
- **SC-002**: 99% of AI attributions complete within 1.5 seconds and include explanation text visible in both languages; any slower response auto-prompts redraw before combat.
- **SC-003**: 100% of recorded battles can be replayed offline to reproduce the published damage log, and any mismatch blocks submission with a remediation checklist.
- **SC-004**: Playable build link and <=90 second demo video remain accessible and up to date for 100% of smoke tests executed the week before submission.
- **SC-005**: Judges completing the guided walkthrough report ≥90% task success (watch match, inspect logs, understand upgrade history) during user testing sessions.

## Assumptions

- Target platform is desktop browser (Chrome/Edge) with drawing tablets or touchpads; mobile support is out of scope for this demo timeline.
- Player matchmaking relies on invite links shared manually among testers; no global lobby discovery is needed.
- Authentication is intentionally omitted; possession of the invite link is the only requirement to join a lobby.
- Hosting will primarily rely on Railway-managed services; offline recap packs act as fallback for judges when Railway access is unavailable.

## Dependencies & Risks

- Requires stable AI inference endpoint capable of batching monster/skill doodles with deterministic seed support; failures stall all gameplay.
- Needs content design for bilingual copy and guided script; delays impact demo readiness even if gameplay works.
- Telemetry + replay pipelines must integrate with submission tracker before final review; missing exports undermine judge trust.
