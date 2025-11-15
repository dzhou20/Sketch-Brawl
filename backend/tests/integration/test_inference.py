from fastapi.testclient import TestClient

from src.api.main import app
from src.services import attribute_store


class MemoryStore:
    def __init__(self) -> None:
        self._tickets: dict[str, dict] = {}

    def persist(self, lobby_id, doodle_type, attributes):
        attributes["lobby_id"] = lobby_id
        attributes["type"] = doodle_type
        return attributes

    def save_ticket(self, payload):
        ticket_id = "ticket-" + str(len(self._tickets) + 1)
        self._tickets[ticket_id] = payload
        return ticket_id

    def get_ticket(self, ticket_id):
        return self._tickets.get(ticket_id)


def test_doodle_flow(monkeypatch):
    attribute_store.get_attribute_store._store = MemoryStore()  # type: ignore[attr-defined]

    class StubTelemetry:
        def publish(self, event):
            return None

    from src.services import telemetry

    telemetry.get_telemetry_service._service = StubTelemetry()  # type: ignore[attr-defined]

    client = TestClient(app)
    payload = {
        "lobby_id": "demo",
        "doodle_type": "monster",
        "strokes": [
            {"x": 10, "y": 10, "timestamp": 0},
            {"x": 11, "y": 12, "timestamp": 1},
        ],
    }
    resp = client.post("/doodles", json=payload)
    assert resp.status_code == 202
    ticket = resp.json()["ticket_id"]

    resp2 = client.get(f"/doodles/{ticket}")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["ticket_id"] == ticket
    assert data["payload"]["lobby_id"] == "demo"
