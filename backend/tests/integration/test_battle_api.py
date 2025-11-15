"""Integration tests for /battles API."""
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

from src.api import battles
from src.api.main import app
from src.infra import database
from src.services.attribute_store import AttributeStore, get_attribute_store
from src.services.battle_service import BattleService

# configure in-memory SQLite for tests (shared across connections)
test_engine = create_engine(
    "sqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
database._engine = test_engine
SQLModel.metadata.create_all(test_engine)
battles.service = BattleService()
get_attribute_store._store = AttributeStore()  # type: ignore[attr-defined]

client = TestClient(app)


def _prepare_monsters(lobby_id: str) -> None:
    store = get_attribute_store()
    store._tickets.clear()  # type: ignore[attr-defined]
    player_a_attrs = {
        "element": "fire",
        "hp": 120,
        "base_attack": 40,
        "seed": 123,
        "explanation": "hot seat",
    }
    player_b_attrs = {
        "element": "water",
        "hp": 110,
        "base_attack": 38,
        "seed": 456,
        "explanation": "hot seat",
    }
    store.persist(
        lobby_id,
        "monster",
        player_a_attrs,
        {"player_slot": "A"},
        snapshot="data:image/png;base64,AAA",
    )
    store.persist(
        lobby_id,
        "monster",
        player_b_attrs,
        {"player_slot": "B"},
        snapshot="data:image/png;base64,BBB",
    )


def test_battle_requires_two_monsters():
    store = get_attribute_store()
    store._tickets.clear()  # type: ignore[attr-defined]

    resp = client.post(
        "/battles",
        json={"lobby_id": "demo-lobby"},
    )
    assert resp.status_code == 400
    assert "Not enough monsters" in resp.json()["detail"]


def test_battle_with_stubbed_monsters():
    lobby_id = "demo-battle"
    _prepare_monsters(lobby_id)

    resp = client.post(
        "/battles",
        json={"lobby_id": lobby_id, "seed": 42},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["winner_slot"] in {"A", "B"}
    assert len(data["timeline"]) > 0
    assert data["combatants"][0]["snapshot"] is not None
    assert len(data["rounds"]) >= 1


def test_battle_summary_rounds_match():
    lobby_id = "demo-battle-summary"
    _prepare_monsters(lobby_id)

    resp = client.post(
        "/battles",
        json={"lobby_id": lobby_id, "seed": 7},
    )
    assert resp.status_code == 200
    battle = resp.json()
    detail = client.get(f"/battles/{battle['battle_id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["rounds"] == battle["rounds"]
    assert detail_body["combatants"] == battle["combatants"]
