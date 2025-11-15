"""Deterministic doodle-to-attribute inference with Gemini/ONNX fallbacks."""
from __future__ import annotations

import logging
from collections import deque
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from src.config import get_settings
from src.services.attribute_store import DoodleType
from src.services.gemini_client import GeminiClient, GeminiError

try:  # pragma: no cover - optional dependency
    from onnxruntime import InferenceSession, SessionOptions
except ImportError:  # pragma: no cover - handled at runtime
    InferenceSession = None  # type: ignore[assignment]
    SessionOptions = None  # type: ignore[assignment]


FALLBACK_ELEMENTS = ["metal", "wood", "water", "fire", "earth"]
MONSTER_ADJECTIVES = ["Rusty", "Hyper", "Sleepy", "Neon", "Ancient", "Bouncy"]
MONSTER_FORMS = ["Bunny", "Golem", "Sprite", "Beetle", "Lizard", "Wisp"]
MONSTER_TITLES = ["Bot", "Beast", "Construct", "Spirit", "Guardian", "Oddity"]
MOVE_VERBS = ["Carrot", "Nebula", "Gear", "Burrow", "Ripple", "Spark"]
MOVE_FORMS = ["Kick", "Shield", "Bash", "Drill", "Beam", "Screen"]
SKILL_NOUNS = ["Pulse", "Barrier", "Torrent", "Hammer", "Loop"]
SKILL_ADJECTIVES = ["Chaotic", "Gleaming", "Whispering", "Irritated", "Stoic"]
SKILL_PHRASES = ["Echo Burst", "Shiny Wall", "Void Hop", "Grumpy Pulse"]


class InferenceRunner:
    """Uses Gemini when configured, ONNX otherwise, and stubs as final fallback."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("service.inference")
        settings = get_settings()
        self._gemini: GeminiClient | None = None
        if settings.gemini_api_key:
            self._gemini = GeminiClient(settings.gemini_api_key, settings.gemini_model)
        self._history: dict[str, deque[dict[str, Any]]] = {
            "Monster": deque(maxlen=6),
            "Skill": deque(maxlen=6),
            "Monster_Enhance": deque(maxlen=6),
            "Skill_Enhance": deque(maxlen=6),
        }

        self._session = None
        if self._gemini is None and InferenceSession is not None:
            model_path = self._resolve_model_path()
            if model_path is not None:
                opts = SessionOptions()
                opts.log_severity_level = 3
                self._session = InferenceSession(str(model_path), sess_options=opts)

    def predict(
        self,
        strokes: list[dict[str, Any]],
        seed: int,
        doodle_type: Optional[DoodleType] = None,
        metadata: Optional[Dict[str, Any]] = None,
        snapshot: str | None = None,
    ) -> dict[str, Any]:
        schema_hint = self._schema_hint(doodle_type, metadata)
        prompt_meta = dict(metadata or {})
        prompt_meta["_hints"] = {
            "recent_results": self._recent_results(schema_hint),
            "stroke_traits": self._stroke_traits(strokes),
            "variety_target": self._variety_target(schema_hint, seed),
        }
        self._logger.info(
            "inference.predict schema=%s seed=%s strokes=%d target=%s",
            schema_hint,
            seed,
            len(strokes),
            metadata.get("target") if metadata else None,
        )
        if self._gemini is not None:
            try:
                result = self._gemini.generate_attributes(
                    strokes,
                    seed,
                    schema_hint=schema_hint,
                    metadata=prompt_meta,
                    snapshot=snapshot,
                )
                self._logger.info(
                    "inference.gemini_success schema=%s seed=%s element=%s hp=%s atk=%s",
                    schema_hint,
                    seed,
                    result["element"],
                    result.get("hp"),
                    result.get("base_attack") or result.get("attack_bonus"),
                )
                self._record_history(schema_hint, result)
                return result
            except GeminiError as exc:
                self._logger.warning(
                    "inference.gemini_failed schema=%s seed=%s reason=%s",
                    schema_hint,
                    seed,
                    exc,
                )

        if self._session is not None:
            latent = self._strokes_to_tensor(strokes)
            outputs = self._session.run(None, {"input": latent})
            raw = outputs[0][0]
            element = self._decode_element(raw[0], seed)
            hp = int(np.clip(raw[1] * 500, 50, 500))
            base_attack = int(np.clip(raw[2] * 100, 5, 100))
            result = {
                "element": element,
                "hp": hp,
                "base_attack": base_attack,
                "skill_type": "weapon",
                "seed": seed,
                "explanation": f"onnx-seed-{seed}",
                "variance": float(abs(raw[3]) if len(raw) > 3 else 0.1),
            }
            self._logger.info(
                "inference.onnx_success schema=%s seed=%s element=%s hp=%s atk=%s",
                schema_hint,
                seed,
                element,
                result.get("hp"),
                result.get("base_attack"),
            )
            self._record_history(schema_hint, result)
            return result

        payload = self._build_stub_payload(schema_hint, strokes, seed)
        self._logger.info(
            "inference.stub schema=%s seed=%s element=%s",
            schema_hint,
            seed,
            payload.get("element"),
        )
        self._record_history(schema_hint, payload)
        return payload

    def _resolve_model_path(self) -> Path | None:
        candidates = [
            Path("backend/models/doodle-classifier.onnx"),
            Path("models/doodle-classifier.onnx"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _strokes_to_tensor(self, strokes: list[dict[str, Any]]) -> np.ndarray:
        tensor = np.zeros((1, 64, 64), dtype=np.float32)
        for stroke in strokes:
            x = int(stroke.get("x", 0)) % 64
            y = int(stroke.get("y", 0)) % 64
            tensor[0, y, x] = min(1.0, tensor[0, y, x] + 0.1)
        return tensor

    def _density(self, strokes: list[dict[str, Any]]) -> float:
        if not strokes:
            return 0.0
        accum = 0.0
        for stroke in strokes:
            accum += float(stroke.get("pressure") or 0.5)
        return accum * 10

    def _decode_element(self, value: float, seed: int) -> str:
        idx = int(abs(value + seed)) % len(FALLBACK_ELEMENTS)
        return FALLBACK_ELEMENTS[idx]

    def _build_stub_payload(
        self,
        schema_hint: str,
        strokes: list[dict[str, Any]],
        seed: int,
    ) -> dict[str, Any]:
        rng = np.random.default_rng(seed)
        density = self._density(strokes)
        element = self._decode_element(density, seed)
        stroke_count = len(strokes)
        if schema_hint == "Monster":
            return self._fallback_monster_payload(rng, element, density, seed, stroke_count)
        if schema_hint == "Skill":
            return self._fallback_skill_payload(rng, element, density, seed, stroke_count)
        if schema_hint == "Monster_Enhance":
            return self._fallback_monster_enhance_payload(rng, element, density, seed, stroke_count)
        return self._fallback_skill_enhance_payload(rng, element, density, seed, stroke_count)

    def _fallback_monster_payload(
        self,
        rng: np.random.Generator,
        element: str,
        density: float,
        seed: int,
        stroke_count: int,
    ) -> dict[str, Any]:
        hp = int(np.clip(160 + density * 2, 50, 500))
        attack = int(np.clip(40 + density * 0.7, 5, 100))
        defense = int(np.clip(35 + density * 0.6, 5, 120))
        name = self._compose_monster_name(rng, element)
        species = self._compose_species(rng)
        descriptor = "dense" if density > 20 else "minimal"
        description = f"A {descriptor} {species.lower()} outlined by {stroke_count} strokes."
        moves = [
            self._compose_move(rng, element, attack, defense, hp, idx)
            for idx in range(2)
        ]
        return {
            "element": element,
            "hp": hp,
            "base_attack": attack,
            "defense": defense,
            "name": name,
            "species": species,
            "description": description,
            "moves": moves,
            "seed": seed,
            "explanation": f"Stubbed from seed={seed} density={density:.1f}.",
        }

    def _fallback_skill_payload(
        self,
        rng: np.random.Generator,
        element: str,
        density: float,
        seed: int,
        stroke_count: int,
    ) -> dict[str, Any]:
        skill_type = rng.choice(["attack", "defense"])
        base_power = int(np.clip(30 + density, 5, 120))
        card_name = f"{rng.choice(SKILL_ADJECTIVES)} {rng.choice(SKILL_NOUNS)}"
        move_name = rng.choice(SKILL_PHRASES)
        description = (
            f"{move_name} channels {element} energy from {stroke_count} quick strokes."
        )
        return {
            "element": element,
            "skill_type": skill_type,
            "attack_bonus": base_power,
            "name": card_name,
            "move_name": move_name,
            "description": description,
            "seed": seed,
            "cooldown_delta": 0,
            "explanation": f"Stubbed skill (seed={seed}) with {skill_type} flavor.",
        }

    def _fallback_monster_enhance_payload(
        self,
        rng: np.random.Generator,
        element: str,
        density: float,
        seed: int,
        stroke_count: int,
    ) -> dict[str, Any]:
        hp_delta = int(np.clip(rng.normal(loc=5, scale=4), -10, 25))
        attack_delta = int(np.clip(rng.normal(loc=3, scale=3), -5, 15))
        defense_delta = int(np.clip(rng.normal(loc=4, scale=3), -5, 15))
        name = f"{rng.choice(MONSTER_ADJECTIVES)} {rng.choice(MONSTER_FORMS)} Evo"
        explanation = (
            f"Extra strokes ({stroke_count}) hinted at more plating, so stats shift modestly."
        )
        return {
            "element": element,
            "hp": hp_delta,
            "base_attack": attack_delta,
            "defense": defense_delta,
            "name": name,
            "seed": seed,
            "explanation": explanation,
        }

    def _fallback_skill_enhance_payload(
        self,
        rng: np.random.Generator,
        element: str,
        density: float,
        seed: int,
        stroke_count: int,
    ) -> dict[str, Any]:
        skill_type = rng.choice(["attack", "defense"])
        power_delta = int(
            np.clip(rng.normal(loc=6 if skill_type == "attack" else 4, scale=4), -5, 25)
        )
        new_name = f"{rng.choice(SKILL_ADJECTIVES)} {rng.choice(SKILL_NOUNS)}+"
        new_move = f"{rng.choice(MOVE_VERBS)} {rng.choice(MOVE_FORMS)} Redux"
        explanation = (
            f"New overlay lines ({stroke_count}) tweak the move toward {skill_type} plays."
        )
        return {
            "element": element,
            "skill_type": skill_type,
            "attack_bonus": power_delta,
            "name": new_name,
            "move_name": new_move,
            "seed": seed,
            "explanation": explanation,
        }

    def _compose_monster_name(self, rng: np.random.Generator, element: str) -> str:
        adj = rng.choice(MONSTER_ADJECTIVES)
        form = rng.choice(MONSTER_FORMS)
        return f"{adj} {element.title()} {form}"

    def _compose_species(self, rng: np.random.Generator) -> str:
        form = rng.choice(MONSTER_FORMS)
        title = rng.choice(MONSTER_TITLES)
        return f"{form} {title}"

    def _compose_move(
        self,
        rng: np.random.Generator,
        element: str,
        attack: int,
        defense: int,
        hp: int,
        index: int,
    ) -> dict[str, Any]:
        verb = rng.choice(MOVE_VERBS)
        noun = rng.choice(MOVE_FORMS)
        kind = rng.choice(["physical", "ranged", "buff", "debuff"])
        base_power = int(np.clip(attack + rng.integers(-10, 15), 10, 60))
        return {
            "name": f"{verb} {noun}",
            "description": f"A {kind} burst that leans on {element} energy.",
            "kind": kind,
            "element": element,
            "power": base_power,
            "attack": max(1, attack - index * 3),
            "defense": max(1, defense - index * 2),
            "health": max(1, hp // (index + 2)),
        }

    def _schema_hint(
        self, doodle_type: Optional[DoodleType], metadata: Optional[Dict[str, Any]]
    ) -> str:
        if doodle_type == "monster":
            return "Monster"
        if doodle_type == "reinforcement":
            target = (metadata or {}).get("target", "skill")
            return "Monster_Enhance" if target == "monster" else "Skill_Enhance"
        return "Skill"

    def _recent_results(self, schema_hint: str) -> list[dict[str, Any]]:
        history = self._history.get(schema_hint)
        if not history:
            return []
        return list(history)[-3:]

    def _record_history(self, schema_hint: str, payload: dict[str, Any]) -> None:
        entry: dict[str, Any] = {}
        if schema_hint == "Monster":
            entry = {
                "element": payload.get("element"),
                "hp": payload.get("hp"),
                "attack": payload.get("base_attack"),
                "name": payload.get("name"),
            }
        elif schema_hint == "Skill":
            entry = {
                "element": payload.get("element"),
                "kind": payload.get("skill_type"),
                "power": payload.get("attack_bonus"),
                "name": payload.get("name"),
            }
        else:
            entry = {
                "element": payload.get("element"),
                "delta_hp": payload.get("hp"),
                "delta_attack": payload.get("base_attack") or payload.get("attack_bonus"),
                "name": payload.get("name"),
            }
        self._history.setdefault(schema_hint, deque(maxlen=6)).append(entry)

    def _stroke_traits(self, strokes: list[dict[str, Any]]) -> dict[str, Any]:
        if not strokes:
            return {"stroke_count": 0, "size": "none", "variance": 0}
        xs = [float(s.get("x", 0.0)) for s in strokes]
        ys = [float(s.get("y", 0.0)) for s in strokes]
        pressures = [float(s.get("pressure") or 0.5) for s in strokes]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        bbox = (round(width, 2), round(height, 2))
        density = round(self._density(strokes), 2)
        avg_pressure = round(sum(pressures) / len(pressures), 2)

        jagged = 0
        total_delta = 0.0
        for prev, curr in zip(strokes, strokes[1:]):
            dx = float(curr.get("x", 0.0)) - float(prev.get("x", 0.0))
            dy = float(curr.get("y", 0.0)) - float(prev.get("y", 0.0))
            delta = abs(dx) + abs(dy)
            total_delta += delta
            if delta > 20:
                jagged += 1
        return {
            "stroke_count": len(strokes),
            "bbox": bbox,
            "density_index": density,
            "avg_pressure": avg_pressure,
            "jagged_segments": jagged,
            "total_motion": round(total_delta, 2),
        }

    def _variety_target(self, schema_hint: str, seed: int) -> str | None:
        if schema_hint not in {"Monster", "Skill"}:
            return None
        history = self._history.get(schema_hint)
        recent = [entry.get("element") for entry in (history or []) if entry.get("element")]
        elements = ["metal", "wood", "water", "fire", "earth"]
        rotated = elements[seed % len(elements) :] + elements[: seed % len(elements)]
        for candidate in rotated:
            if candidate not in recent[-2:]:
                return candidate
        return None


_runner: InferenceRunner | None = None


def get_runner() -> InferenceRunner:
    global _runner
    if _runner is None:
        _runner = InferenceRunner()
    return _runner
