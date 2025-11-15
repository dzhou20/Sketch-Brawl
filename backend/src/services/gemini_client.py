"""Gemini API client for doodle-to-attribute inference."""
from __future__ import annotations

import json
from typing import Any, Dict, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.services.prompt_manager import build_prompt

Element = Literal["metal", "wood", "water", "fire", "earth"]
SkillKind = Literal["attack", "defense"]


class GeminiError(RuntimeError):
    """Raised when Gemini API fails."""


class MonsterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    element: Element
    health: int = Field(ge=60, le=140)
    attack: int = Field(ge=10, le=50)
    defense: int = Field(ge=10, le=50)
    name: str | None = None
    explanation: str


class SkillResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: SkillKind
    element: Element
    power: int = Field(ge=10, le=60)
    name: str | None = None
    move_name: str | None = None
    explanation: str


class MonsterEnhanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    add_element: Element | None = None
    add_health: int = Field(ge=-10, le=25)
    add_attack: int = Field(ge=-5, le=15)
    add_defense: int = Field(ge=-5, le=15)
    new_name: str | None = None
    explanation: str


class SkillEnhanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    add_kind: SkillKind
    add_element: Element | None = None
    add_power: int = Field(ge=-5, le=25)
    new_name: str | None = None
    new_move_name: str | None = None
    explanation: str


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._client = httpx.Client(timeout=40)

    def generate_attributes(
        self,
        strokes: list[dict[str, Any]],
        seed: int,
        schema_hint: str,
        metadata: Dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": self._prompt(strokes, seed, schema_hint, metadata or {}),
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "topK": 32,
            },
        }

        url = f"{self._base_url}/models/{self._model}:generateContent"
        response = self._client.post(url, params={"key": self._api_key}, json=body)
        if response.status_code >= 400:
            raise GeminiError(f"Gemini error {response.status_code}: {response.text}")
        payload = response.json()
        text = (
            payload.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return self._parse_attributes(text, seed, schema_hint)

    def _prompt(
        self,
        strokes: list[dict[str, Any]],
        seed: int,
        schema_hint: str,
        metadata: Dict[str, Any],
    ) -> str:
        return build_prompt(schema_hint, strokes, seed, metadata)

    def _parse_attributes(self, text: str, seed: int, schema_hint: str) -> dict[str, Any]:
        cleaned = self._strip_fence(text)
        cleaned = self._maybe_unwrap(cleaned, schema_hint)
        try:
            if schema_hint == "Skill":
                attrs = SkillResponse.model_validate_json(cleaned)
                return {
                    "element": attrs.element,
                    "skill_type": attrs.kind,
                    "attack_bonus": attrs.power,
                    "name": attrs.name or "Unnamed Skill",
                    "move_name": attrs.move_name or "Unnamed Move",
                    "seed": seed,
                    "explanation": attrs.explanation,
                }
            if schema_hint == "Monster_Enhance":
                attrs = MonsterEnhanceResponse.model_validate_json(cleaned)
                return {
                    "element": attrs.add_element or "fire",
                    "hp": attrs.add_health,
                    "base_attack": attrs.add_attack,
                    "defense": attrs.add_defense,
                    "name": attrs.new_name or "Enhanced Monster",
                    "seed": seed,
                    "explanation": attrs.explanation,
                }
            if schema_hint == "Skill_Enhance":
                attrs = SkillEnhanceResponse.model_validate_json(cleaned)
                return {
                    "element": attrs.add_element or "fire",
                    "skill_type": attrs.add_kind,
                    "attack_bonus": attrs.add_power,
                    "name": attrs.new_name or "Enhanced Skill",
                    "move_name": attrs.new_move_name or "Enhanced Move",
                    "seed": seed,
                    "explanation": attrs.explanation,
                }
            attrs = MonsterResponse.model_validate_json(cleaned)
            return {
                "element": attrs.element,
                "hp": max(50, min(500, int(attrs.health))),
                "base_attack": max(5, min(100, int(attrs.attack))),
                "defense": attrs.defense,
                "name": attrs.name or "Unnamed Monster",
                "seed": seed,
                "explanation": attrs.explanation,
            }
        except (ValidationError, json.JSONDecodeError) as exc:
            raise GeminiError(f"Gemini output invalid: {cleaned}") from exc

    def _strip_fence(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 2:
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                stripped = "\n".join(lines)
            else:
                stripped = stripped.strip("`")
        return stripped.strip()

    def _maybe_unwrap(self, text: str, schema_hint: str) -> str:
        """Some generations add a root key ("monster": {...}). Unwrap if detected."""
        stripped = text.strip()
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return stripped

        key = schema_hint.lower()
        if key in payload and isinstance(payload[key], dict):
            return json.dumps(payload[key], ensure_ascii=False)
        return stripped
