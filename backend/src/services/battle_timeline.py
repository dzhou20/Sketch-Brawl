"""Helpers for building battle timeline summaries."""
from __future__ import annotations

from typing import Dict, List

from src.services.battle_engine import BattleEvent, BattleResult, Combatant


class BattleTimelineBuilder:
    """Builds UI-ready payloads from raw battle events."""

    def build_payload(
        self,
        combatants: List[Combatant],
        result: BattleResult,
    ) -> Dict[str, object]:
        events = [event.__dict__ for event in result.timeline]
        rounds = self._round_summaries(result.timeline, combatants)
        data = {
            "winner_slot": result.winner_slot,
            "wins": dict(result.wins),
            "timeline": events,
            "rounds": rounds,
            "combatants": [self._serialize_combatant(c) for c in combatants],
        }
        return data

    def _round_summaries(
        self,
        events: List[BattleEvent],
        combatants: List[Combatant],
    ) -> List[dict]:
        grouped: Dict[int, List[BattleEvent]] = {}
        for event in events:
            grouped.setdefault(event.round, []).append(event)
        summaries: List[dict] = []
        base_hp = {combatant.slot: combatant.base_hp for combatant in combatants}
        for round_idx in sorted(grouped):
            entries = grouped[round_idx]
            damage_totals = {slot: 0 for slot in base_hp.keys()}
            hp_state = dict(base_hp)
            winner_slot = ""
            ko_turn = None
            turns = 0
            for entry in entries:
                if entry.event == "round_end":
                    if not winner_slot:
                        winner_slot = entry.attacker
                    continue
                turns += 1
                damage_totals[entry.attacker] = damage_totals.get(entry.attacker, 0) + entry.damage
                hp_state[entry.defender] = entry.defender_hp
                if entry.event == "ko" and not winner_slot:
                    winner_slot = entry.attacker
                    ko_turn = turns
            summaries.append(
                {
                    "round": round_idx,
                    "winner_slot": winner_slot,
                    "turns": turns,
                    "ko_turn": ko_turn,
                    "total_damage": damage_totals,
                    "hp_remaining": hp_state,
                }
            )
        return summaries

    def _serialize_combatant(self, combatant: Combatant) -> dict:
        return {
            "slot": combatant.slot,
            "name": combatant.name,
            "element": combatant.element,
            "base_hp": combatant.base_hp,
            "base_attack": combatant.base_attack,
            "skill_power": combatant.skill_power,
            "snapshot": combatant.snapshot,
            "skills": combatant.skills or [],
        }
