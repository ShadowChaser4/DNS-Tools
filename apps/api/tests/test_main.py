"""Tests for root and health endpoints."""

from unittest.mock import AsyncMock, MagicMock


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "DNS Tools API" in data["message"]


def test_health_ok(client, mock_mongo_db: MagicMock):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["message"] == "API is running smoothly."
    mock_mongo_db.command.assert_awaited_once_with("ping")


def test_health_mongo_failure(client, mock_mongo_db: MagicMock):
    mock_mongo_db.command = AsyncMock(side_effect=RuntimeError("connection refused"))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["message"] == "API is not running smoothly"
