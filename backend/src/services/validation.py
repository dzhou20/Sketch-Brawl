"""Skill reinforcement validation rules."""
from __future__ import annotations

from typing import Sequence


class ValidationError(Exception):
    pass


def validate_elements(elements: Sequence[str]) -> None:
    if len(elements) > 3:
        raise ValidationError("max 3 elements per skill")


def validate_attack_bonus(attack_bonus: int) -> None:
    if attack_bonus < 0 or attack_bonus > 50:
        raise ValidationError("attack bonus must be between 0 and 50")


def validate_cooldown(delta: int) -> None:
    if delta < -2 or delta > 2:
        raise ValidationError("cooldown delta must be between -2 and +2")


def validate_reinforcement(payload: dict) -> None:
    elements = payload.get("elements", [])
    attack_bonus = payload.get("attack_bonus", 0)
    cooldown_delta = payload.get("cooldown_delta", 0)
    validate_elements(elements)
    validate_attack_bonus(int(attack_bonus))
    validate_cooldown(int(cooldown_delta))
