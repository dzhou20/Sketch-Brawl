"""Skill history helpers for upgrade tracking."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict


def build_history_entry(
    doodle_type: str,
    attributes: Dict[str, Any],
    metadata: Dict[str, Any],
) -> str:
    """Create a compact JSON string describing the latest skill change."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "doodle_type": doodle_type,
        "player_slot": metadata.get("player_slot"),
        "target": metadata.get("target"),
        "element": attributes.get("element"),
        "skill_type": attributes.get("skill_type"),
        "attack_bonus": attributes.get("attack_bonus"),
        "hp": attributes.get("hp"),
        "base_attack": attributes.get("base_attack"),
        "seed": attributes.get("seed"),
    }
    return json.dumps(entry, ensure_ascii=False)
