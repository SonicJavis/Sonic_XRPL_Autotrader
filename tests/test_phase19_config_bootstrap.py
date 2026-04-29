from app.config import Settings
from app.live.xrpl_ingestion_bootstrap import initialize_xrpl_ingestion
from app.main import create_app


def test_ingestion_disabled_by_default() -> None:
    settings = Settings()

    assert settings.XRPL_INGESTION_ENABLED is False
    assert settings.XRPL_INGESTION_MODE == "disabled"
    assert settings.XRPL_SHADOW_SOURCE == "static"


def test_bootstrap_disabled_has_no_snapshot_source() -> None:
    app = create_app()

    health = initialize_xrpl_ingestion(app)

    assert health.ingestion_enabled is False
    assert app.state.snapshot_source is None
    assert app.state.ingestion_mode == "disabled"


def test_invalid_config_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("XRPL_INGESTION_ENABLED", "true")
    monkeypatch.setenv("XRPL_INGESTION_MODE", "live_shadow")
    monkeypatch.setenv("XRPL_SHADOW_SOURCE", "invalid")
    app = create_app()

    health = initialize_xrpl_ingestion(app)

    assert health.reason == "INGESTION_INVALID_CONFIG"
    assert app.state.snapshot_source is None


def test_replay_bootstrap_attaches_source(monkeypatch) -> None:
    monkeypatch.setenv("XRPL_INGESTION_ENABLED", "true")
    monkeypatch.setenv("XRPL_INGESTION_MODE", "replay")
    monkeypatch.setenv("XRPL_SHADOW_SOURCE", "replay")
    app = create_app()

    health = initialize_xrpl_ingestion(app)

    assert health.ingestion_enabled is True
    assert app.state.snapshot_source is not None
    assert app.state.ingestion_mode == "replay"
