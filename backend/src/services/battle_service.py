"""Service layer for orchestrating hot-seat battles."""
from __future__ import annotations

import json
import logging
import random
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from src.infra.database import get_engine
from src.models.battle_session import BattleSession
from src.models.monster import Monster, SkillCard
from src.services.battle_engine import BattleEngine, Combatant
from src.services.battle_timeline import BattleTimelineBuilder


class BattleService:
    def __init__(self) -> None:
        self._engine = get_engine()
        self._timeline_builder = BattleTimelineBuilder()
        self._logger = logging.getLogger("service.battle")

    def start_battle(self, lobby_id: str, seed: Optional[int] = None) -> Dict[str, Any]:
        self._logger.info("battle.start lobby=%s seed=%s", lobby_id, seed)
        with Session(self._engine) as session:
            monsters = self._load_latest_monsters(session, lobby_id)
            if len(monsters) < 2:
                raise ValueError("Not enough monsters to start a battle. Draw monsters for both players first.")
            combatants = self._build_combatants(session, monsters)
            rng_seed = seed or random.randint(0, 10**9)
            engine = BattleEngine(rng_seed)
            result = engine.run_match(combatants)
            payload = self._timeline_builder.build_payload(combatants, result)
            battle_row = BattleSession(
                lobby_id=lobby_id,
                rng_seed=str(rng_seed),
                rounds=payload["timeline"],
                summary={
                    "rounds": payload["rounds"],
                    "wins": payload["wins"],
                    "winner_slot": payload["winner_slot"],
                },
                combatants=payload["combatants"],
                winner_player_id=result.winner_slot,
                state="completed",
            )
            session.add(battle_row)
            session.commit()
            session.refresh(battle_row)
            response = dict(payload)
            response["battle_id"] = battle_row.id
            self._logger.info(
                "battle.completed lobby=%s seed=%s winner=%s battle_id=%s",
                lobby_id,
                rng_seed,
                result.winner_slot,
                battle_row.id,
            )
            return response

    def get_battle(self, battle_id: int) -> Optional[BattleSession]:
        self._logger.info("battle.fetch battle_id=%s", battle_id)
        with Session(self._engine) as session:
            return session.get(BattleSession, battle_id)

    def _load_latest_monsters(self, session: Session, lobby_id: str) -> Dict[str, Monster]:
        stmt = (
            select(Monster)
            .where(Monster.match_id == lobby_id)
            .order_by(Monster.id.desc())
        )
        records = session.exec(stmt).all()
        slots: Dict[str, Monster] = {}
        for monster in records:
            slot = self._player_slot(monster.player_id)
            if slot not in slots:
                slots[slot] = monster
            if len(slots) >= 2:
                break
        return slots

    def _build_combatants(
        self, session: Session, monsters: Dict[str, Monster]
    ) -> List[Combatant]:
        ordered_slots = sorted(monsters.keys())
        monster_ids = [monster.id for monster in monsters.values() if monster.id is not None]
        skills_map = self._load_skills(session, monster_ids)
        combatants: List[Combatant] = []
        for slot in ordered_slots:
            monster = monsters[slot]
            combatants.append(self._to_combatant(slot, monster, skills_map))
        return combatants

    def _player_slot(self, player_id: str) -> str:
        if ":" in player_id:
            return player_id.split(":", 1)[1]
        return player_id or "A"

    def _to_combatant(
        self,
        slot: str,
        monster: Monster,
        skills_map: Dict[int, List[SkillCard]],
    ) -> Combatant:
        raw_skills = skills_map.get(monster.id or 0, [])
        skills = [
            {
                "id": skill.id,
                "type": skill.type,
                "elements": skill.elements,
                "attack_bonus": skill.attack_bonus,
                "history": skill.history,
                "cooldown_delta": skill.cooldown_delta,
            }
            for skill in raw_skills
        ]
        deltas = self._aggregate_skill_deltas(raw_skills)
        return Combatant(
            slot=slot,
            name=monster.name,
            element=monster.element,
            base_hp=max(1, monster.hp + deltas.get("hp_delta", 0)),
            base_attack=max(1, monster.base_attack + deltas.get("attack_delta", 0)),
            skill_power=max(5, deltas.get("skill_power", 10)),
            snapshot=monster.snapshot_data,
            skills=skills,
        )

    def _load_skills(
        self, session: Session, monster_ids: List[int]
    ) -> Dict[int, List[SkillCard]]:
        if not monster_ids:
            return {}
        stmt = (
            select(SkillCard)
            .where(SkillCard.monster_id.in_(monster_ids))
            .order_by(SkillCard.id.asc())
        )
        skills = session.exec(stmt).all()
        grouped: Dict[int, List[SkillCard]] = {}
        for skill in skills:
            grouped.setdefault(skill.monster_id, []).append(skill)
        return grouped

    def _aggregate_skill_deltas(self, skills: List[SkillCard]) -> Dict[str, int]:
        summary = {"hp_delta": 0, "attack_delta": 0, "skill_power": 10}
        if not skills:
            return summary
        base_power = max(skill.attack_bonus for skill in skills if skill.attack_bonus is not None) or 0
        history_bonus = 0
        hp_delta = 0
        atk_delta = 0
        for skill in skills:
            if skill.history:
                for entry in skill.history:
                    try:
                        payload = json.loads(entry)
                    except (TypeError, json.JSONDecodeError):
                        continue
                    history_bonus += int(payload.get("attack_bonus") or 0)
                    hp_delta += int(payload.get("hp") or 0)
                    atk_delta += int(payload.get("base_attack") or 0)
        summary["skill_power"] = max(5, base_power + history_bonus)
        summary["hp_delta"] = hp_delta
        summary["attack_delta"] = atk_delta
        return summary
