<!--
Sync Impact Report
Version change: -- -> 1.0.0
Modified principles:
- N/A (initial constitution)
Added sections:
- Core Principles
- AI + Gameplay Technical Constraints
- Development Workflow & Review Gates
- Governance
Removed sections:
- None
Templates requiring updates:
- updated game/.specify/templates/plan-template.md
- updated game/.specify/templates/spec-template.md
- updated game/.specify/templates/tasks-template.md
Follow-up TODOs:
- None
-->
# Sketch Brawl Constitution

## Core Principles

### I. Doodle Input Fidelity
The drawing canvas MUST feel instantaneous on commodity laptops (<=50 ms stroke latency,
>=60 fps) and operate identically for both players. Stroke data, timestamps, and seed
values MUST be persisted so any round can be replayed deterministically. Input errors
or dropped frames MUST be surfaced through UI cues and telemetry within 5 seconds so a
round can be restarted before the battle begins. This guarantees that the "skill of
sketching" remains the strategic axis instead of fighting the UI.

### II. Transparent AI Attribution
Every AI inference MUST output the interpreted attributes (element, HP, base attack,
skill type, naming) plus a short explanation string that can be shown in the UI and is
logged for judges. Inference requests MUST complete within 1.5 seconds and are replayed
via stored prompts + seed so the same doodle always yields the same attributes during
judging. Model updates require a published change note describing new behavior and new
regression doodles to verify neutrality across art styles.

### III. Deterministic Auto-Battle Loop
Battles MUST derive all damage, elemental reactions, and win conditions from the saved
attributes and a single RNG seed so any match can be simulated offline for verification.
Best-of-three structure, health resets, and round timers MUST be enforced by the
server--not the client--to prevent tampering. Each damage event, KO, and overtime call
is logged and available for replay tools used in demo videos.

### IV. Persistent Skill Evolution
Skill cards accumulate upgrades between rounds, but stacking rules MUST remain explicit:
max three elements per skill, additive attack bonuses capped by AI-evaluated complexity,
and cooldown adjustments declared in the log. Reinforcement doodles MUST reference their
parent skill IDs so history is traceable. If validation fails, the UI MUST block the
upgrade and explain which rule was violated, ensuring fairness across multi-round play.

### V. Demo-Ready Delivery
A playable build (web link or packaged app) and a <=90 second walkthrough video MUST be
kept current at all times because the AI hackathon submission depends on them. Builds
MUST include instructions for connecting two players remotely, a spectate mode for
judges, and a fallback "guided battle" script for offline capture. Any feature merged to
main MUST confirm that both the build link and the demo script still work end to end.

## AI + Gameplay Technical Constraints

- Client rendering targets 1920x1080 but MUST gracefully degrade to 1280x720 without
  breaking pen accuracy. UI text MUST remain bilingual-ready so instructions can be
  localized for judges.
- AI inference hosts MUST expose a health endpoint and support batch processing of the
  four canonical doodle types (monster, weapon, shield, augment). Cold starts may not
  exceed 5 seconds.
- Battle resolution MUST finish within 10 seconds per round, even when every skill stacks
  the maximum allowed effects. Performance budgets MUST be captured in specs and tests.
- Telemetry MUST capture: canvas device info, inference latency, battle duration, win/loss
  outcome, and any validation failures. Analytics dumps power the submission recap deck.

## Development Workflow & Review Gates

1. Feature specs enumerate which principles they touch and list metrics proving
   compliance (latency, inference time, determinism checks, and demo deliverables).
2. Implementation plans MUST include a Constitution Check gate covering input fidelity,
   AI transparency, deterministic battles, upgrade validation, and demo readiness before
   coding begins.
3. Tasks are grouped by user story so each slice can be demoed independently; at least
   one task per story MUST cover telemetry/log updates that keep replay data trustworthy.
4. Pull requests MUST link to updated telemetry dashboards or manual test evidence and
   confirm that the playable link + video script were smoke-tested after the change.

## Governance

This constitution is the definitive source of delivery rules for Sketch Brawl. Any
amendment requires approval from both the gameplay owner and the AI systems owner.
Version changes follow semantic versioning: MAJOR for rewritten principles or removed
sections, MINOR for additional principles or new governance constraints, PATCH for
clarifications. Every amendment MUST update affected templates (plan, spec, tasks) and
record the new version in this file. Compliance is enforced during plan reviews and
again during pull requests via the Constitution Check gate; submissions lacking evidence
for the five principles cannot merge.

**Version**: 1.0.0 | **Ratified**: 2025-11-15 | **Last Amended**: 2025-11-15
