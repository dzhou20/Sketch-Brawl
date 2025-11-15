# Data Model — Sketch Brawl Demo Delivery

## Monster
- **Fields**: `id (UUID)`, `player_id`, `match_id`, `name`, `element`, `hp`, `base_attack`, `seed`, `ai_explanation`, `created_at`
- **Relationships**: 1:Many with `SkillCard`; belongs to `BattleSession`
- **Validation**: `hp` within 50-500; `base_attack` within 5-100; `element` must be from controlled vocabulary {fire, water, earth, air, light, shadow}; `seed` immutable per session
- **State Notes**: Created after AI inference; immutable except for audit fields

## SkillCard
- **Fields**: `id (UUID)`, `monster_id`, `type (weapon|shield|augment)`, `elements[]`, `attack_bonus`, `cooldown_delta`, `history (array of reinforcement doodle refs)`, `seed`, `ai_explanation`, `created_at`, `updated_at`
- **Relationships**: Many-to-1 with `Monster`; history entries reference `TelemetryEvent`
- **Validation**: `elements` length <= 3; `attack_bonus` capped at +50; `cooldown_delta` between -2 and +2 turns; new reinforcement requires matching parent `monster_id`
- **State Notes**: Upgrades append to `history` with deterministic order; invalid submissions rejected with reason codes

## BattleSession
- **Fields**: `id (UUID)`, `lobby_id`, `rng_seed`, `rounds[]`, `winner_player_id`, `replay_uri`, `state (pending|in_progress|completed|invalid)`, `created_at`, `completed_at`
- **Relationships**: References two `Monster` records per round, includes derived `SkillCard` snapshots
- **Validation**: `rng_seed` stored as 64-bit int; `rounds` array holds deterministic log entries (timestamp, attacker, defender, damage, status)
- **State Notes**: Only server mutates; invalid state triggered if replay diff fails integrity check

## TelemetryEvent
- **Fields**: `id (UUID)`, `session_id`, `source (frontend|backend|worker)`, `type (canvas_latency|inference_time|validation_error|battle_runtime|demo_asset)`, `payload JSONB`, `captured_at`
- **Relationships**: Linked to `BattleSession`/`Monster`/`SkillCard` via `session_id`
- **Validation**: `payload` schema validated per type (e.g., canvas latency requires percentile distribution); events older than 30 days archived
- **State Notes**: Drives dashboards + constitution evidence; emitted via telemetry service

## DemoArtifact
- **Fields**: `id (UUID)`, `type (playable_build|walkthrough_video|offline_bundle)`, `version`, `uri`, `checksum`, `generated_from_commit`, `status (active|deprecated)`, `created_at`
- **Relationships**: Linked to CI deployment metadata + `BattleSession` sample logs included
- **Validation**: `version` increments semver; `checksum` required for offline verification
- **State Notes**: On each merge to main, new artifact generated and flagged active once smoke tests pass
