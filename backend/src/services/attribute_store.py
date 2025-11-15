"""Persist monsters/skills + inference tickets."""
from __future__ import annotations

import uuid
from typing import Any, Literal

from sqlmodel import Session

from src.infra.database import get_engine
from src.models.monster import Monster, SkillCard
from src.services.skill_history import build_history_entry

DoodleType = Literal["monster", "skill", "reinforcement"]


class AttributeStore:
    def __init__(self) -> None:
        self._engine = get_engine()
        self._tickets: dict[str, dict[str, Any]] = {}

    def persist(
        self,
        lobby_id: str,
        doodle_type: DoodleType,
        attributes: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        snapshot: str | None = None,
    ) -> dict[str, Any]:
        metadata = metadata or {}
        player_slot = metadata.get("player_slot") or metadata.get("player") or "A"
        player_id = f"{lobby_id}:{player_slot}" if ":" not in str(player_slot) else player_slot

        with Session(self._engine) as session:
            if doodle_type == "monster":
                monster = Monster(
                    player_id=player_id,
                    match_id=lobby_id,
                    name=attributes.get("name", "Sketch Beast"),
                    element=attributes.get("element", "fire"),
                    hp=int(attributes.get("hp", 100)),
                    base_attack=int(attributes.get("base_attack", 40)),
                    seed=str(attributes.get("seed")),
                    ai_explanation=attributes.get("explanation"),
                    snapshot_data=snapshot,
                )
                session.add(monster)
                session.commit()
                session.refresh(monster)
                attributes["monster_id"] = monster.id
                if snapshot:
                    attributes["snapshot"] = snapshot
            else:
                monster_id = int(attributes.get("monster_id") or metadata.get("monster_id") or 0)
                if doodle_type == "reinforcement":
                    skill_id = metadata.get("skill_id")
                    if not skill_id:
                        raise ValueError("Reinforcement requires an existing skill_id")
                    skill = session.get(SkillCard, int(skill_id))
                    if not skill:
                        raise ValueError("Skill not found for reinforcement")
                    self._apply_reinforcement(skill, attributes, metadata)
                    session.add(skill)
                    session.commit()
                    session.refresh(skill)
                    attributes["skill_id"] = skill.id
                    attributes["monster_id"] = skill.monster_id
                else:
                    skill = SkillCard(
                        monster_id=monster_id,
                        type=attributes.get("skill_type", "weapon"),
                        elements=attributes.get("elements", [attributes.get("element", "fire")]),
                        attack_bonus=int(attributes.get("attack_bonus", 0)),
                        cooldown_delta=int(attributes.get("cooldown_delta", 0)),
                        seed=str(attributes.get("seed")),
                        history=[],
                        explanation=attributes.get("explanation"),
                    )
                    session.add(skill)
                    session.commit()
                    session.refresh(skill)
                    attributes["skill_id"] = skill.id
        return attributes

    def _apply_reinforcement(
        self,
        skill: SkillCard,
        attributes: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        history_entry = build_history_entry("reinforcement", attributes, metadata)
        if history_entry:
            existing = list(skill.history or [])
            existing.append(history_entry)
            skill.history = existing
        delta_attack = int(attributes.get("attack_bonus") or 0)
        if delta_attack:
            skill.attack_bonus = max(0, skill.attack_bonus + delta_attack)
        delta_cooldown = attributes.get("cooldown_delta")
        if delta_cooldown is not None:
            skill.cooldown_delta = max(-2, min(2, skill.cooldown_delta + int(delta_cooldown)))
        new_element = attributes.get("element")
        if new_element:
            elements = list(skill.elements or [])
            if new_element not in elements and len(elements) < 3:
                elements.append(new_element)
            skill.elements = elements
        return attributes

    def save_ticket(self, payload: dict[str, Any]) -> str:
        ticket_id = uuid.uuid4().hex
        self._tickets[ticket_id] = payload
        return ticket_id

    def get_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        return self._tickets.get(ticket_id)


def get_attribute_store() -> AttributeStore:
    # simple singleton
    if not hasattr(get_attribute_store, "_store"):
        get_attribute_store._store = AttributeStore()  # type: ignore[attr-defined]
    return get_attribute_store._store  # type: ignore[attr-defined]
