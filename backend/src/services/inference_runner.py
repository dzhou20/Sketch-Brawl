"""Deterministic doodle-to-attribute inference with Gemini/ONNX fallbacks."""
from __future__ import annotations

import logging
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


class InferenceRunner:
    """Uses Gemini when configured, ONNX otherwise, and stubs as final fallback."""

    def __init__(self) -> None:
        settings = get_settings()
        self._gemini: GeminiClient | None = None
        if settings.gemini_api_key:
            self._gemini = GeminiClient(settings.gemini_api_key, settings.gemini_model)

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
    ) -> dict[str, Any]:
        schema_hint = self._schema_hint(doodle_type, metadata)
        if self._gemini is not None:
            try:
                result = self._gemini.generate_attributes(
                    strokes,
                    seed,
                    schema_hint=schema_hint,
                    metadata=metadata or {},
                )
                logger = logging.getLogger("battle.inference")
                logger.info(
                    "Gemini success schema=%s seed=%s element=%s hp=%s atk=%s",
                    schema_hint,
                    seed,
                    result["element"],
                    result["hp"],
                    result["base_attack"],
                )
                return result
            except GeminiError as exc:
                print(f"[gemini] falling back to ONNX/stub: {exc}")

        if self._session is not None:
            latent = self._strokes_to_tensor(strokes)
            outputs = self._session.run(None, {"input": latent})
            raw = outputs[0][0]
            element = self._decode_element(raw[0], seed)
            hp = int(np.clip(raw[1] * 500, 50, 500))
            base_attack = int(np.clip(raw[2] * 100, 5, 100))
            return {
                "element": element,
                "hp": hp,
                "base_attack": base_attack,
                "skill_type": "weapon",
                "seed": seed,
                "explanation": f"onnx-seed-{seed}",
                "variance": float(abs(raw[3]) if len(raw) > 3 else 0.1),
            }

        # fallback stub
        rng = np.random.default_rng(seed)
        density = self._density(strokes)
        element = self._decode_element(density, seed)
        hp = int(np.clip(200 + density * 3, 50, 500))
        base_attack = int(np.clip(40 + density * 0.6, 5, 100))
        explanation = f"seed={seed} density={density} strokes={len(strokes)}"
        payload = {
            "element": element,
            "hp": hp,
            "base_attack": base_attack,
            "seed": seed,
            "explanation": explanation,
            "variance": float(rng.random()),
        }
        if schema_hint.startswith("Skill"):
            payload["skill_type"] = rng.choice(["attack", "defense"])
            payload["attack_bonus"] = base_attack
        else:
            payload["skill_type"] = "weapon"
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
        elements = ["fire", "water", "earth", "air", "light", "shadow"]
        idx = int(abs(value + seed)) % len(elements)
        return elements[idx]

    def _schema_hint(
        self, doodle_type: Optional[DoodleType], metadata: Optional[Dict[str, Any]]
    ) -> str:
        if doodle_type == "monster":
            return "Monster"
        if doodle_type == "reinforcement":
            target = (metadata or {}).get("target", "skill")
            return "Monster_Enhance" if target == "monster" else "Skill_Enhance"
        return "Skill"


_runner: InferenceRunner | None = None


def get_runner() -> InferenceRunner:
    global _runner
    if _runner is None:
        _runner = InferenceRunner()
    return _runner
