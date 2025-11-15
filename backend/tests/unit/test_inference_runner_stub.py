from __future__ import annotations

import pytest

from src import config
from src.services.inference_runner import InferenceRunner


@pytest.fixture()
def stub_runner(monkeypatch) -> InferenceRunner:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    config.get_settings.cache_clear()
    runner = InferenceRunner()
    runner._gemini = None  # type: ignore[attr-defined]
    runner._session = None  # type: ignore[attr-defined]
    return runner


def _strokes() -> list[dict]:
    return [
        {"x": 10, "y": 10, "pressure": 0.6, "timestamp": 0},
        {"x": 14, "y": 12, "pressure": 0.8, "timestamp": 1},
    ]


def test_stub_monster_payload_is_rich(stub_runner: InferenceRunner):
    result = stub_runner.predict(_strokes(), seed=42, doodle_type="monster")
    assert result["hp"] >= 50
    assert result["base_attack"] >= 5
    assert result["defense"] >= 5
    assert result["species"]
    assert result["description"]
    assert isinstance(result["moves"], list) and result["moves"]
    first_move = result["moves"][0]
    assert first_move["name"]
    assert first_move["kind"]
    assert first_move["element"] in {"metal", "wood", "water", "fire", "earth"}
    assert "power" in first_move


def test_stub_skill_payload_has_names_and_description(stub_runner: InferenceRunner):
    result = stub_runner.predict(_strokes(), seed=7, doodle_type="skill")
    assert result["skill_type"] in {"attack", "defense"}
    assert result["attack_bonus"] >= 5
    assert result["name"]
    assert result["move_name"]
    assert result["description"]


def test_stub_skill_reinforcement_payload(stub_runner: InferenceRunner):
    metadata = {"target": "skill"}
    result = stub_runner.predict(_strokes(), seed=99, doodle_type="reinforcement", metadata=metadata)
    assert result["skill_type"] in {"attack", "defense"}
    assert "attack_bonus" in result
    assert result["name"]
    assert result["move_name"]


def test_stub_monster_reinforcement_payload(stub_runner: InferenceRunner):
    metadata = {"target": "monster"}
    result = stub_runner.predict(_strokes(), seed=5, doodle_type="reinforcement", metadata=metadata)
    assert "hp" in result
    assert "base_attack" in result
    assert "defense" in result
    assert result["name"]
