"""Gemini API client for doodle-to-attribute inference."""
from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Dict, Literal, Tuple

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.services.prompt_manager import build_prompt

Element = Literal["metal", "wood", "water", "fire", "earth"]
SkillKind = Literal["attack", "defense"]


class GeminiError(RuntimeError):
    """Raised when Gemini API fails."""


class MonsterMove(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    description: str | None = None
    kind: str | None = None
    element: Element | None = None
    power: int | None = None


class MonsterResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    element: Element
    health: int = Field(ge=1, le=1000)
    attack: int = Field(ge=1, le=500)
    defense: int = Field(ge=1, le=500)
    name: str | None = None
    explanation: str | None = None
    species: str | None = None
    description: str | None = None
    moves: list[MonsterMove] | None = None


class SkillResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: SkillKind
    element: Element
    power: int = Field(ge=1, le=200)
    name: str | None = None
    move_name: str | None = None
    description: str | None = None
    explanation: str | None = None


class MonsterEnhanceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    add_element: Element | None = None
    add_health: int = Field(ge=-10, le=25)
    add_attack: int = Field(ge=-5, le=15)
    add_defense: int = Field(ge=-5, le=15)
    new_name: str | None = None
    explanation: str | None = None


class SkillEnhanceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    add_kind: SkillKind
    add_element: Element | None = None
    add_power: int = Field(ge=-5, le=25)
    new_name: str | None = None
    new_move_name: str | None = None
    explanation: str | None = None


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
        snapshot: str | None = None,
    ) -> dict[str, Any]:
        image_part, snapshot_hint = self._inline_image(snapshot)
        prompt_text = self._prompt(strokes, seed, schema_hint, metadata or {}, snapshot_hint)
        parts: list[dict[str, Any]] = []
        if image_part:
            parts.append(image_part)
        parts.append({"text": prompt_text})
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": parts,
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "topK": 32,
            },
        }

        url = f"{self._base_url}/models/{self._model}:generateContent"
        try:
            response = self._client.post(url, params={"key": self._api_key}, json=body)
        except httpx.HTTPError as exc:
            raise GeminiError(f"Gemini request failed: {exc}") from exc
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
        snapshot_hint: str | None = None,
    ) -> str:
        return build_prompt(schema_hint, strokes, seed, metadata, snapshot_hint=snapshot_hint)

    def _inline_image(self, snapshot: str | None) -> Tuple[dict[str, Any] | None, str | None]:
        if not snapshot:
            return None, None
        data = snapshot
        mime = "image/png"
        if snapshot.startswith("data:"):
            header, _, rest = snapshot.partition(",")
            data = rest
            mime = header.split(";")[0].split(":")[1] if ":" in header else mime
        if not data:
            return None, None
        hint = None
        try:
            decoded = base64.b64decode(data, validate=False)
            digest = hashlib.sha1(decoded).hexdigest()[:10]
            hint = f"{mime} bytes={len(decoded)} sha1={digest}"
        except Exception:  # pragma: no cover
            hint = f"{mime} base64_len={len(data)}"
        return (
            {
                "inline_data": {
                    "mime_type": mime,
                    "data": data,
                }
            },
            hint,
        )

    def _ensure_explanation(self, raw: str | None, schema_hint: str) -> str:
        if raw and raw.strip():
            return raw
        return f"{schema_hint} response missing explanation from Gemini."

    def _parse_attributes(self, text: str, seed: int, schema_hint: str) -> dict[str, Any]:
        cleaned = self._strip_fence(text)
        cleaned = self._maybe_unwrap(cleaned, schema_hint)
        normalized = self._normalize_for_schema(cleaned, schema_hint)
        try:
            if schema_hint == "Skill":
                attrs = SkillResponse.model_validate_json(normalized)
                description = attrs.description
                return {
                    "element": attrs.element,
                    "skill_type": attrs.kind,
                    "attack_bonus": attrs.power,
                    "name": attrs.name or "Unnamed Skill",
                    "move_name": attrs.move_name or "Unnamed Move",
                    "description": description,
                    "seed": seed,
                    "explanation": self._ensure_explanation(attrs.explanation or description, schema_hint),
                }
            if schema_hint == "Monster_Enhance":
                attrs = MonsterEnhanceResponse.model_validate_json(normalized)
                return {
                    "element": attrs.add_element or "fire",
                    "hp": attrs.add_health,
                    "base_attack": attrs.add_attack,
                    "defense": attrs.add_defense,
                    "name": attrs.new_name or "Enhanced Monster",
                    "seed": seed,
                    "explanation": self._ensure_explanation(attrs.explanation, schema_hint),
                }
            if schema_hint == "Skill_Enhance":
                attrs = SkillEnhanceResponse.model_validate_json(normalized)
                return {
                    "element": attrs.add_element or "fire",
                    "skill_type": attrs.add_kind,
                    "attack_bonus": attrs.add_power,
                    "name": attrs.new_name or "Enhanced Skill",
                    "move_name": attrs.new_move_name or "Enhanced Move",
                    "seed": seed,
                    "explanation": self._ensure_explanation(attrs.explanation, schema_hint),
                }
            attrs = MonsterResponse.model_validate_json(normalized)
            moves = [
                move.model_dump(exclude_none=True) for move in (attrs.moves or []) if move is not None
            ]
            description = attrs.description or attrs.explanation
            return {
                "element": attrs.element,
                "hp": max(50, min(500, int(attrs.health))),
                "base_attack": max(5, min(100, int(attrs.attack))),
                "defense": attrs.defense,
                "name": attrs.name or "Unnamed Monster",
                "species": attrs.species,
                "description": description,
                "moves": moves or None,
                "seed": seed,
                "explanation": self._ensure_explanation(attrs.explanation or description, schema_hint),
            }
        except (ValidationError, json.JSONDecodeError) as exc:
            raise GeminiError(f"Gemini output invalid: {cleaned}") from exc

    def _normalize_for_schema(self, text: str, schema_hint: str) -> str:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text
        if not isinstance(payload, dict):
            return text
        normalized = dict(payload)
        if schema_hint == "Monster":
            normalized = self._normalize_monster_payload(normalized)
        elif schema_hint == "Skill":
            normalized = self._normalize_skill_payload(normalized)
        elif schema_hint == "Monster_Enhance":
            normalized = self._normalize_monster_enhance_payload(normalized)
        elif schema_hint == "Skill_Enhance":
            normalized = self._normalize_skill_enhance_payload(normalized)
        return json.dumps(normalized, ensure_ascii=False)

    def _normalize_monster_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        attributes = payload.get("attributes")
        if isinstance(attributes, dict):
            if "health" not in payload and "health_points" in attributes:
                payload["health"] = attributes["health_points"]
            if "attack" not in payload:
                for key in ("attack_points", "attack"):
                    if key in attributes:
                        payload["attack"] = attributes[key]
                        break
            if "defense" not in payload:
                for key in ("defense_points", "defense"):
                    if key in attributes:
                        payload["defense"] = attributes[key]
                        break
        if "moves" not in payload and isinstance(payload.get("skills"), list):
            payload["moves"] = payload["skills"]
        if "health" not in payload and "hp" in payload:
            payload["health"] = payload["hp"]
        if "attack" not in payload and "base_attack" in payload:
            payload["attack"] = payload["base_attack"]
        if "defense" not in payload and "defence" in payload:
            payload["defense"] = payload["defence"]
        if "explanation" not in payload and payload.get("description"):
            payload["explanation"] = payload["description"]
        moves = payload.get("moves")
        if isinstance(moves, list):
            normalized_moves: list[dict[str, Any]] = []
            for move in moves:
                if isinstance(move, dict):
                    entry = dict(move)
                    if "power" not in entry:
                        for candidate in ("attack", "strength", "damage"):
                            if candidate in entry:
                                entry["power"] = entry[candidate]
                                break
                    normalized_moves.append(entry)
            payload["moves"] = normalized_moves
        if "health" not in payload and "health_points" in payload:
            payload["health"] = payload["health_points"]
        if "attack" not in payload and "attack_points" in payload:
            payload["attack"] = payload["attack_points"]
        if "defense" not in payload and "defense_points" in payload:
            payload["defense"] = payload["defense_points"]
        return payload

    def _normalize_skill_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if "kind" not in payload:
            for candidate in ("skill_type", "type", "category"):
                if candidate in payload:
                    payload["kind"] = payload[candidate]
                    break
        if "power" not in payload:
            for candidate in ("attack_bonus", "attack", "damage", "strength"):
                if candidate in payload:
                    payload["power"] = payload[candidate]
                    break
        if "element" not in payload:
            elements = payload.get("elements")
            if isinstance(elements, list) and elements:
                payload["element"] = elements[0]
        if "explanation" not in payload and payload.get("description"):
            payload["explanation"] = payload["description"]
        return payload

    def _normalize_monster_enhance_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if "add_health" not in payload and "hp" in payload:
            payload["add_health"] = payload["hp"]
        if "add_attack" not in payload and "attack" in payload:
            payload["add_attack"] = payload["attack"]
        if "add_defense" not in payload and "defense" in payload:
            payload["add_defense"] = payload["defense"]
        if "explanation" not in payload and payload.get("description"):
            payload["explanation"] = payload["description"]
        return payload

    def _normalize_skill_enhance_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if "add_kind" not in payload and payload.get("skill_type"):
            payload["add_kind"] = payload["skill_type"]
        if "add_power" not in payload:
            for candidate in ("attack_bonus", "attack", "damage"):
                if candidate in payload:
                    payload["add_power"] = payload[candidate]
                    break
        if "explanation" not in payload and payload.get("description"):
            payload["explanation"] = payload["description"]
        return payload

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
        """Unwrap payloads that add a root key (e.g., {"monster": {...}})."""
        stripped = text.strip()
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return stripped

        key = schema_hint.lower()
        if key in payload and isinstance(payload[key], dict):
            return json.dumps(payload[key], ensure_ascii=False)
        return stripped
