"""Deterministic hot-seat battle engine for Sketch Brawl."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Combatant:
    slot: str
    name: str
    element: str
    base_hp: int
    base_attack: int
    skill_power: int = 10
    snapshot: Optional[str] = None
    skills: Optional[List[dict]] = None

    def defense(self) -> int:
        return max(5, min(80, int(self.base_attack * 0.4) + 10))


@dataclass
class BattleEvent:
    round: int
    turn: int
    attacker: str
    defender: str
    damage: int
    defender_hp: int
    event: str


@dataclass
class RoundResult:
    winner_slot: str
    events: List[BattleEvent]


@dataclass
class BattleResult:
    winner_slot: str
    wins: Dict[str, int]
    timeline: List[BattleEvent]


class BattleEngine:
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.random = random.Random(seed)

    def run_match(self, combatants: List[Combatant]) -> BattleResult:
        if len(combatants) != 2:
            raise ValueError("Battle engine requires exactly two combatants")
        wins: Dict[str, int] = {combatants[0].slot: 0, combatants[1].slot: 0}
        timeline: List[BattleEvent] = []
        round_idx = 1
        while max(wins.values()) < 2 and round_idx <= 3:
            round_seed = self.random.randint(0, 10**9)
            result = self._simulate_round(combatants, round_idx, round_seed)
            wins[result.winner_slot] += 1
            timeline.extend(result.events)
            timeline.append(
                BattleEvent(
                    round=round_idx,
                    turn=len(result.events) + 1,
                    attacker=result.winner_slot,
                    defender="-",
                    damage=0,
                    defender_hp=0,
                    event="round_end",
                )
            )
            round_idx += 1
        winner = max(wins, key=lambda slot: wins[slot])
        return BattleResult(winner_slot=winner, wins=wins, timeline=timeline)

    def _simulate_round(
        self, combatants: List[Combatant], round_idx: int, round_seed: int
    ) -> RoundResult:
        rng = random.Random(round_seed)
        states = {
            combatants[0].slot: combatants[0].base_hp,
            combatants[1].slot: combatants[1].base_hp,
        }
        order = combatants[:]
        # alternate starting attacker per round
        if round_idx % 2 == 0:
            order = list(reversed(order))
        events: List[BattleEvent] = []
        turn_idx = 1
        while all(hp > 0 for hp in states.values()):
            attacker = order[0 if turn_idx % 2 == 1 else 1]
            defender = order[1 if attacker is order[0] else 0]
            damage = self._calculate_damage(attacker, defender, rng)
            states[defender.slot] -= damage
            events.append(
                BattleEvent(
                    round=round_idx,
                    turn=turn_idx,
                    attacker=attacker.slot,
                    defender=defender.slot,
                    damage=damage,
                    defender_hp=max(0, states[defender.slot]),
                    event="ko" if states[defender.slot] <= 0 else "hit",
                )
            )
            if states[defender.slot] <= 0:
                return RoundResult(winner_slot=attacker.slot, events=events)
            turn_idx += 1
        # fallback (should not reach)
        return RoundResult(winner_slot=order[0].slot, events=events)

    def _calculate_damage(self, attacker: Combatant, defender: Combatant, rng: random.Random) -> int:
        attack_roll = attacker.base_attack + attacker.skill_power
        defense = defender.defense()
        variance = rng.randint(-3, 5)
        element_bonus = self._element_bonus(attacker.element, defender.element)
        return max(5, attack_roll - defense + variance + element_bonus)

    def _element_bonus(self, attacker_element: str, defender_element: str) -> int:
        chart = {
            "fire": "wood",
            "wood": "earth",
            "earth": "metal",
            "metal": "water",
            "water": "fire",
        }
        if chart.get(attacker_element) == defender_element:
            return 5
        if chart.get(defender_element) == attacker_element:
            return -5
        return 0
