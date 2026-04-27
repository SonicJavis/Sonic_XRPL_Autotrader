"""Tests for the FastAPI health endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "bot_mode" in data
    assert data["live_trading_enabled"] is False


def test_health_config(client):
    resp = client.get("/health/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "bot_mode" in data
    assert "max_trade_xrp" in data
