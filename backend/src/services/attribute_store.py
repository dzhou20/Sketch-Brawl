"""Persist monsters/skills + inference tickets."""
from __future__ import annotations

import uuid
from typing import Any, Literal

from sqlmodel import Session

from src.infra.database import get_engine
from src.models.monster import Monster, SkillCard

DoodleType = Literal["monster", "skill", "reinforcement"]


class AttributeStore:
    def __init__(self) -> None:
        self._engine = get_engine()
        self._tickets: dict[str, dict[str, Any]] = {}

    def persist(self, lobby_id: str, doodle_type: DoodleType, attributes: dict[str, Any]) -> dict[str, Any]:
        with Session(self._engine) as session:
            if doodle_type == "monster":
                monster = Monster(
                    player_id=lobby_id,
                    match_id=lobby_id,
                    name=attributes.get("name", "Sketch Beast"),
                    element=attributes["element"],
                    hp=attributes["hp"],
                    base_attack=attributes["base_attack"],
                    seed=str(attributes["seed"]),
                    ai_explanation=attributes.get("explanation"),
                )
                session.add(monster)
                session.commit()
                session.refresh(monster)
                attributes["monster_id"] = monster.id
            else:
                skill = SkillCard(
                    monster_id=attributes.get("monster_id", 0),
                    type=attributes.get("skill_type", "weapon"),
                    elements=attributes.get("elements", [attributes["element"]]),
                    attack_bonus=attributes.get("attack_bonus", 0),
                    cooldown_delta=attributes.get("cooldown_delta", 0),
                    seed=str(attributes["seed"]),
                    history=[],
                    explanation=attributes.get("explanation"),
                )
                session.add(skill)
                session.commit()
                session.refresh(skill)
                attributes["skill_id"] = skill.id
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
