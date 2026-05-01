from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.config.runtime_mode import validate_runtime_or_raise
from app.config import Settings


def _prod_env(monkeypatch, *, token: str = "test-token", origins: str = "https://dashboard.example") -> None:
    monkeypatch.setenv("ENV_MODE", "PRODUCTION")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("EXECUTION_ENABLED", "false")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("API_AUTH_TOKEN", token)
    monkeypatch.setenv("ALLOWED_ORIGINS", origins)
    monkeypatch.setenv("XRPL_INGESTION_MODE", "disabled")
    monkeypatch.setenv("XRPL_SHADOW_SOURCE", "static")


def test_production_requires_auth_for_all_non_health_endpoints(monkeypatch) -> None:
    _prod_env(monkeypatch)
    app = create_app()
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["validated_data_only"] is True
    assert health.json()["is_executable"] is False

    blocked = client.get("/validation/live/status")
    assert blocked.status_code == 401
    assert blocked.json()["is_executable"] is False

    allowed = client.get("/validation/live/status", headers={"X-API-Token": "test-token"})
    assert allowed.status_code == 200
    assert allowed.json()["is_executable"] is False


def test_bearer_auth_and_metrics_are_safe(monkeypatch) -> None:
    _prod_env(monkeypatch)
    client = TestClient(create_app())

    body = client.get("/metrics", headers={"Authorization": "Bearer test-token"}).json()

    assert body["is_executable"] is False
    assert body["is_shadow"] is True
    assert body["decay_staleness_summary"]["validated_data_only"] is True
    assert "latest_validated_ledger_index" in body


def test_production_config_fails_closed_for_unsafe_values(monkeypatch) -> None:
    _prod_env(monkeypatch, token="")
    try:
        validate_runtime_or_raise(Settings())
    except RuntimeError as exc:
        assert "API_AUTH_TOKEN" in str(exc)
    else:
        raise AssertionError("production without auth token must fail closed")

    _prod_env(monkeypatch, origins="*")
    try:
        validate_runtime_or_raise(Settings())
    except RuntimeError as exc:
        assert "wildcard CORS" in str(exc)
    else:
        raise AssertionError("production wildcard CORS must fail closed")

    _prod_env(monkeypatch)
    monkeypatch.setenv("EXECUTION_ENABLED", "true")
    try:
        validate_runtime_or_raise(Settings())
    except RuntimeError as exc:
        assert "execution flags" in str(exc)
    else:
        raise AssertionError("production execution flag must fail closed")


def test_invalid_runtime_mode_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("ENV_MODE", "UNKNOWN")

    try:
        validate_runtime_or_raise(Settings())
    except RuntimeError as exc:
        assert "ENV_MODE" in str(exc)
    else:
        raise AssertionError("invalid runtime mode must fail closed")


def test_cors_restrictions_and_security_headers(monkeypatch) -> None:
    _prod_env(monkeypatch, origins="https://dashboard.example")
    client = TestClient(create_app())

    allowed = client.options(
        "/validation/live/status",
        headers={
            "Origin": "https://dashboard.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Token",
        },
    )
    denied = client.options(
        "/validation/live/status",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Token",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == "https://dashboard.example"
    assert "access-control-allow-origin" not in denied.headers
    assert allowed.headers["x-content-type-options"] == "nosniff"
    assert allowed.headers["x-frame-options"] == "DENY"


def test_rate_limit_is_basic_and_fail_closed(monkeypatch) -> None:
    _prod_env(monkeypatch)
    monkeypatch.setenv("API_RATE_LIMIT_PER_MINUTE", "1")
    client = TestClient(create_app())

    first = client.get("/metrics", headers={"X-API-Token": "test-token"})
    second = client.get("/metrics", headers={"X-API-Token": "test-token"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["is_executable"] is False


def test_public_payloads_do_not_expose_raw_xrpl_fields(monkeypatch) -> None:
    _prod_env(monkeypatch)
    client = TestClient(create_app())

    body = client.get("/validation/intents", headers={"X-API-Token": "test-token"}).json()
    encoded = str(body).lower()

    assert "raw book_offers" not in encoded
    assert "raw amm_info" not in encoded
    assert body["is_executable"] is False
