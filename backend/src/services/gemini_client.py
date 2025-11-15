"""Gemini API client for doodle-to-attribute inference."""
from __future__ import annotations

import base64
import hashlib
import json
import logging
from typing import Any, Dict, Literal, Tuple

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.services.prompt_manager import build_prompt

Element = Literal["metal", "wood", "water", "fire", "earth"]
SkillKind = Literal["attack", "defense"]
_ALLOWED_ELEMENTS = {"metal", "wood", "water", "fire", "earth"}
_ELEMENT_SYNONYMS = {
    "electric": "metal",
    "lightning": "metal",
    "shock": "metal",
    "air": "wood",
    "wind": "wood",
    "ice": "water",
    "nature": "wood",
    "stone": "earth",
    "rock": "earth",
}

FUNCTION_DECLARATIONS: Dict[str, Dict[str, Any]] = {
    "Monster": {
        "name": "createMonster",
        "description": "Return a monster payload following the schema.",
        "parameters": {
            "type": "object",
            "properties": {
                "element": {"type": "string", "enum": list(_ALLOWED_ELEMENTS)},
                "health": {"type": "integer"},
                "attack": {"type": "integer"},
                "defense": {"type": "integer"},
                "name": {"type": "string"},
                "species": {"type": "string"},
                "description": {"type": "string"},
                "moves": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "kind": {"type": "string"},
                            "element": {"type": "string"},
                            "power": {"type": "number"},
                        },
                        "required": ["name", "element"],
                    },
                },
                "explanation": {"type": "string"},
            },
            "required": ["element", "health", "attack", "defense"],
        },
    },
    "Skill": {
        "name": "createSkill",
        "description": "Return a skill payload following the schema.",
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["attack", "defense"]},
                "element": {"type": "string"},
                "power": {"type": "integer"},
                "name": {"type": "string"},
                "move_name": {"type": "string"},
                "description": {"type": "string"},
                "explanation": {"type": "string"},
            },
            "required": ["kind", "element", "power"],
        },
    },
    "Monster_Enhance": {
        "name": "createMonsterEnhance",
        "description": "Return monster enhancement deltas.",
        "parameters": {
            "type": "object",
            "properties": {
                "add_element": {"type": "string"},
                "add_health": {"type": "integer"},
                "add_attack": {"type": "integer"},
                "add_defense": {"type": "integer"},
                "new_name": {"type": "string"},
                "explanation": {"type": "string"},
            },
            "required": ["add_health", "add_attack", "add_defense"],
        },
    },
    "Skill_Enhance": {
        "name": "createSkillEnhance",
        "description": "Return skill enhancement deltas.",
        "parameters": {
            "type": "object",
            "properties": {
                "add_kind": {"type": "string"},
                "add_element": {"type": "string"},
                "add_power": {"type": "integer"},
                "new_name": {"type": "string"},
                "new_move_name": {"type": "string"},
                "explanation": {"type": "string"},
            },
            "required": ["add_kind", "add_power"],
        },
    },
}


class GeminiError(RuntimeError):
    """Raised when Gemini API fails."""


class MonsterMove(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = None
    description: str | None = None
    kind: str | None = None
    element: Element | None = None
    power: int | None = None
    attack: int | None = None
    defense: int | None = None
    health: int | None = None


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
    add_health: int = Field(ge=-1000, le=1000)
    add_attack: int = Field(ge=-500, le=500)
    add_defense: int = Field(ge=-500, le=500)
    new_name: str | None = None
    explanation: str | None = None


class SkillEnhanceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    add_kind: SkillKind
    add_element: Element | None = None
    add_power: int = Field(ge=-500, le=500)
    new_name: str | None = None
    new_move_name: str | None = None
    explanation: str | None = None


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._client = httpx.Client(timeout=40)
        self._logger = logging.getLogger("service.gemini")

    def generate_attributes(
        self,
        strokes: list[dict[str, Any]],
        seed: int,
        schema_hint: str,
        metadata: Dict[str, Any] | None = None,
        snapshot: str | None = None,
    ) -> dict[str, Any]:
        self._logger.info(
            "gemini.request schema=%s seed=%s strokes=%d snapshot=%s",
            schema_hint,
            seed,
            len(strokes),
            bool(snapshot),
        )
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
        function_decl = FUNCTION_DECLARATIONS.get(schema_hint)
        if function_decl:
            body["tools"] = [{"functionDeclarations": [function_decl]}]
            body["toolConfig"] = {
                "functionCallingConfig": {
                    "mode": "ANY",
                    "allowedFunctionNames": [function_decl["name"]],
                }
            }

        url = f"{self._base_url}/models/{self._model}:generateContent"
        try:
            response = self._client.post(url, params={"key": self._api_key}, json=body)
        except httpx.HTTPError as exc:
            self._logger.error(
                "gemini.http_error schema=%s seed=%s reason=%s",
                schema_hint,
                seed,
                exc,
            )
            raise GeminiError(f"Gemini request failed: {exc}") from exc
        if response.status_code >= 400:
            self._logger.error(
                "gemini.bad_status schema=%s seed=%s status=%s body=%s",
                schema_hint,
                seed,
                response.status_code,
                response.text[:500],
            )
            raise GeminiError(f"Gemini error {response.status_code}: {response.text}")
        payload = response.json()
        function_args = self._extract_function_call(payload)
        if function_args is not None:
            text = json.dumps(function_args, ensure_ascii=False)
        else:
            text = (
                payload.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
        result = self._parse_attributes(text, seed, schema_hint)
        self._logger.info(
            "gemini.response schema=%s seed=%s element=%s hp=%s atk=%s",
            schema_hint,
            seed,
            result.get("element"),
            result.get("hp"),
            result.get("base_attack") or result.get("attack_bonus"),
        )
        return result

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

    @staticmethod
    def _clamp_int(value: Any, lower: int, upper: int, default: int | None = None) -> int:
        if value is None:
            value = default if default is not None else lower
        try:
            number = int(value)
        except (TypeError, ValueError):
            try:
                number = int(float(value))
            except (TypeError, ValueError):
                number = default if default is not None else lower
        return max(lower, min(upper, number))

    def _parse_attributes(self, text: str, seed: int, schema_hint: str) -> dict[str, Any]:
        cleaned = self._strip_fence(text)
        cleaned = self._maybe_unwrap(cleaned, schema_hint)
        normalized = self._normalize_for_schema(cleaned, schema_hint)
        try:
            if schema_hint == "Skill":
                attrs = SkillResponse.model_validate_json(normalized)
                description = attrs.description
                attack_bonus = self._clamp_int(attrs.power, 5, 120)
                return {
                    "element": attrs.element,
                    "skill_type": attrs.kind,
                    "attack_bonus": attack_bonus,
                    "name": attrs.name or "Unnamed Skill",
                    "move_name": attrs.move_name or "Unnamed Move",
                    "description": description,
                    "seed": seed,
                    "explanation": self._ensure_explanation(attrs.explanation or description, schema_hint),
                }
            if schema_hint == "Monster_Enhance":
                attrs = MonsterEnhanceResponse.model_validate_json(normalized)
                hp_delta = self._clamp_int(attrs.add_health, -10, 25, 0)
                attack_delta = self._clamp_int(attrs.add_attack, -5, 15, 0)
                defense_delta = self._clamp_int(attrs.add_defense, -5, 15, 0)
                return {
                    "element": attrs.add_element or "fire",
                    "hp": hp_delta,
                    "base_attack": attack_delta,
                    "defense": defense_delta,
                    "name": attrs.new_name or "Enhanced Monster",
                    "seed": seed,
                    "explanation": self._ensure_explanation(attrs.explanation, schema_hint),
                }
            if schema_hint == "Skill_Enhance":
                attrs = SkillEnhanceResponse.model_validate_json(normalized)
                power_delta = self._clamp_int(attrs.add_power, -5, 25, 0)
                return {
                    "element": attrs.add_element or "fire",
                    "skill_type": attrs.add_kind,
                    "attack_bonus": power_delta,
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
            hp_value = self._clamp_int(attrs.health, 50, 500)
            attack_value = self._clamp_int(attrs.attack, 5, 100)
            defense_value = self._clamp_int(attrs.defense, 5, 120)
            return {
                "element": attrs.element,
                "hp": hp_value,
                "base_attack": attack_value,
                "defense": defense_value,
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
            self._ensure_field(payload, "health", ["health_points"], attributes)
            self._ensure_field(payload, "attack", ["attack_points", "attack"], attributes)
            self._ensure_field(payload, "defense", ["defense_points", "defense"], attributes)
        element = payload.get("element") or payload.get("type")
        payload["element"] = self._coerce_element(element)
        if "moves" not in payload and isinstance(payload.get("skills"), list):
            payload["moves"] = payload["skills"]
        self._ensure_field(payload, "health", ["hp", "power_level"], payload)
        self._ensure_field(payload, "attack", ["base_attack", "power", "power_level"], payload)
        self._ensure_field(payload, "defense", ["defence", "stamina", "armor", "power_level"], payload)
        if "explanation" not in payload and payload.get("description"):
            payload["explanation"] = payload["description"]
        moves = payload.get("moves")
        if isinstance(moves, list):
            normalized_moves: list[dict[str, Any]] = []
            for move in moves:
                if isinstance(move, dict):
                    entry = dict(move)
                    entry["element"] = self._coerce_element(entry.get("element") or payload["element"])
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
        payload["kind"] = self._coerce_skill_kind(payload.get("kind"))
        if "power" not in payload:
            for candidate in ("attack_bonus", "attack", "damage", "strength"):
                if candidate in payload:
                    payload["power"] = payload[candidate]
                    break
        if "element" not in payload:
            elements = payload.get("elements")
            if isinstance(elements, list) and elements:
                payload["element"] = elements[0]
        payload["element"] = self._coerce_element(payload.get("element") or payload.get("type"))
        if "name" not in payload and payload.get("title"):
            payload["name"] = payload["title"]
        if "name" not in payload and payload.get("title"):
            payload["name"] = payload["title"]
        self._ensure_field(payload, "power", ["attack_bonus", "power_level", "powerValue"], payload)
        self._ensure_field(payload, "name", ["card_name"], payload)
        self._ensure_field(payload, "move_name", ["shout", "callout"], payload)
        if "explanation" not in payload and payload.get("description"):
            payload["explanation"] = payload["description"]
        return payload

    def _extract_function_call(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        candidates = payload.get("candidates") or []
        for candidate in candidates:
            content = candidate.get("content") or {}
            parts = content.get("parts") or []
            for part in parts:
                function_call = part.get("functionCall")
                if not function_call:
                    continue
                args = function_call.get("args")
                if args is None:
                    return {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        return {}
                if isinstance(args, dict):
                    return args
        return None

    def _normalize_monster_enhance_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if "add_health" not in payload and "hp" in payload:
            payload["add_health"] = payload["hp"]
        if "add_attack" not in payload and "attack" in payload:
            payload["add_attack"] = payload["attack"]
        if "add_defense" not in payload and "defense" in payload:
            payload["add_defense"] = payload["defense"]
        self._ensure_field(payload, "add_health", ["power", "power_level"], payload)
        self._ensure_field(payload, "add_attack", ["power", "attack_bonus"], payload)
        self._ensure_field(payload, "add_defense", ["armor", "shielding"], payload)
        if payload.get("add_element") is None and payload.get("element"):
            payload["add_element"] = payload["element"]
        if payload.get("add_element"):
            payload["add_element"] = self._coerce_element(payload["add_element"])
        if "explanation" not in payload and payload.get("description"):
            payload["explanation"] = payload["description"]
        return payload

    def _normalize_skill_enhance_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if "add_kind" not in payload and payload.get("skill_type"):
            payload["add_kind"] = payload["skill_type"]
        self._ensure_field(payload, "add_kind", ["skill_enhance_type", "type", "kind"], payload)
        payload["add_kind"] = self._coerce_skill_kind(payload.get("add_kind"))
        if "add_power" not in payload:
            for candidate in ("attack_bonus", "attack", "damage"):
                if candidate in payload:
                    payload["add_power"] = payload[candidate]
                    break
        self._ensure_field(
            payload,
            "add_power",
            ["power", "power_level", "delta_attack", "delta_power", "delta_damage"],
            payload,
        )
        if payload.get("add_element") is None and payload.get("element"):
            payload["add_element"] = payload["element"]
        if payload.get("add_element"):
            payload["add_element"] = self._coerce_element(payload["add_element"])
        if "explanation" not in payload and payload.get("description"):
            payload["explanation"] = payload["description"]
        return payload

    def _ensure_field(
        self,
        target: dict[str, Any],
        field: str,
        candidates: list[str],
        source: dict[str, Any],
    ) -> None:
        if field in target and target[field] not in (None, ""):
            return
        for candidate in candidates:
            if candidate in source and source[candidate] not in (None, ""):
                target[field] = source[candidate]
                return

    def _coerce_element(self, raw: str | None) -> str:
        if not raw:
            return "metal"
        lowered = raw.strip().lower()
        if lowered in _ALLOWED_ELEMENTS:
            return lowered
        if lowered in _ELEMENT_SYNONYMS:
            return _ELEMENT_SYNONYMS[lowered]
        for key, value in _ELEMENT_SYNONYMS.items():
            if key in lowered:
                return value
        return "metal"

    def _coerce_skill_kind(self, raw: str | None) -> SkillKind:
        if not raw:
            return "attack"
        lowered = str(raw).strip().lower()
        if lowered in {"attack", "offense", "offensive"}:
            return "attack"
        if lowered in {"defense", "defensive", "shield"}:
            return "defense"
        return "attack"

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
