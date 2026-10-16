"""Тесты бизнес-логики Chess Trainer API."""
import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, engine
from server import app


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def test_health(client):
    """GET /health должен возвращать ok."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_root(client):
    """GET / возвращает приветствие."""
    r = client.get("/")
    assert r.status_code == 200
    assert "message" in r.json()


def test_create_game(client):
    """POST /api/v1/games создаёт партию."""
    r = client.post("/api/v1/games", json={
        "player_name": "TestPlayer",
        "opponent": "TestBot",
        "result": "win",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["player_name"] == "TestPlayer"
    assert data["opponent"] == "TestBot"
    assert data["result"] == "win"
    assert "id" in data


def test_get_game_by_id(client):
    """GET /api/v1/games/{id} возвращает партию."""
    r1 = client.post("/api/v1/games", json={
        "player_name": "P1", "opponent": "B1", "result": "lose"
    })
    gid = r1.json()["id"]
    r2 = client.get(f"/api/v1/games/{gid}")
    assert r2.status_code == 200
    assert r2.json()["id"] == gid


def test_game_not_found(client):
    """GET /api/v1/games/999999 → 404."""
    r = client.get("/api/v1/games/999999")
    assert r.status_code == 404


def test_create_user(client):
    """POST /api/v1/users создаёт пользователя."""
    r = client.post("/api/v1/users", json={
        "external_id": "test_unique_001",
        "platform": "telegram",
        "username": "tester",
        "first_name": "Тест",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["external_id"] == "test_unique_001"


def test_create_event(client):
    """POST /api/v1/events создаёт событие."""
    r = client.post("/api/v1/events", json={
        "source": "telegram",
        "event_type": "command",
        "user_external_id": "test_001",
        "payload": {"command": "/start"},
    })
    assert r.status_code == 200
    assert r.json()["source"] == "telegram"


def test_stats(client):
    """GET /api/v1/stats возвращает статистику."""
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_users" in data
    assert "total_games" in data
    assert "total_events" in data


def test_random_game(client):
    """GET /api/v1/games/random возвращает партию."""
    client.post("/api/v1/games", json={
        "player_name": "Rand", "opponent": "Bot"
    })
    r = client.get("/api/v1/games/random")
    assert r.status_code == 200
    assert "id" in r.json()