"""Shallow scenario smoke tests — intentionally weak."""

from fastapi.testclient import TestClient

from app.main import app
from app.seed import seed


def setup_module() -> None:
    seed(reset=True)


client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["scenario"] == "thesis-tracker"


def test_api_login_coordinator():
    r = client.post(
        "/api/auth/login",
        json={"email": "coord@example.com", "password": "coord-dev"},
    )
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "coordinator"
    assert "password" not in r.json()["user"]


def test_pairings_list():
    r = client.get("/api/pairings")
    assert r.status_code == 200
    assert len(r.json()["pairings"]) >= 1
