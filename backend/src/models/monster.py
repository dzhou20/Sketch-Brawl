"""Monster + SkillCard SQLModel definitions."""

from typing import List, Optional

from sqlalchemy import JSON, Text
from sqlmodel import Column, Field, Relationship, SQLModel


class SkillCardBase(SQLModel):
    type: str = Field(index=True)
    elements: list[str] = Field(sa_column=Column(JSON))
    attack_bonus: int = Field(default=0, ge=0, le=50)
    cooldown_delta: int = Field(default=0, ge=-2, le=2)
    history: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    explanation: Optional[str] = None


class Monster(SQLModel, table=True):
    __tablename__ = "monsters"

    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: str = Field(index=True)
    match_id: str = Field(index=True)
    name: str
    element: str = Field(index=True)
    hp: int = Field(ge=50, le=500)
    base_attack: int = Field(ge=5, le=100)
    seed: str = Field(index=True)
    ai_explanation: Optional[str] = None
    snapshot_data: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    skills: List["SkillCard"] = Relationship(back_populates="monster")


class SkillCard(SkillCardBase, table=True):
    __tablename__ = "skill_cards"

    id: Optional[int] = Field(default=None, primary_key=True)
    monster_id: int = Field(foreign_key="monsters.id", index=True)
    seed: str = Field(index=True)
    monster: Optional["Monster"] = Relationship(back_populates="skills")
