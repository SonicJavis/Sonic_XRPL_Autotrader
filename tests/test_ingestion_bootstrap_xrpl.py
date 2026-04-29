from types import SimpleNamespace

from app.config import Settings
from app.live.shadow_snapshot_source import StaticShadowSnapshotSource
from app.live.xrpl_ingestion_bootstrap import initialize_xrpl_ingestion


def _app(settings: Settings, source=None):
    state = SimpleNamespace(container=SimpleNamespace(settings=settings))
    if source is not None:
        state.snapshot_source = source
    return SimpleNamespace(state=state)


def test_disabled_bootstrap_leaves_no_adapter() -> None:
    app = _app(Settings(_env_file=None))

    health = initialize_xrpl_ingestion(app)

    assert health.reason == "INGESTION_DISABLED"
    assert app.state.ingestion_adapter is None
    assert app.state.xrpl_ingestion_adapter is None
    assert app.state.snapshot_source is None


def test_replay_bootstrap_uses_replay_only_and_is_idempotent() -> None:
    app = _app(Settings(_env_file=None, XRPL_INGESTION_ENABLED=True, XRPL_INGESTION_MODE="replay", XRPL_SHADOW_SOURCE="replay"))

    first = initialize_xrpl_ingestion(app)
    second = initialize_xrpl_ingestion(app)

    assert first.reason == "INGESTION_READY"
    assert second.reason == "INGESTION_READY"
    assert app.state.ingestion_mode == "replay"
    assert app.state.ingestion_adapter is app.state.snapshot_source


def test_xrpl_ws_without_injected_source_fails_closed() -> None:
    app = _app(Settings(_env_file=None, XRPL_INGESTION_ENABLED=True, XRPL_INGESTION_MODE="live_shadow", XRPL_SHADOW_SOURCE="xrpl_ws"))

    health = initialize_xrpl_ingestion(app)

    assert health.reason == "INGESTION_SOURCE_UNAVAILABLE"
    assert app.state.ingestion_adapter is None


def test_xrpl_ws_with_injected_source_does_not_connect() -> None:
    injected = StaticShadowSnapshotSource([])
    app = _app(
        Settings(_env_file=None, XRPL_INGESTION_ENABLED=True, XRPL_INGESTION_MODE="live_shadow", XRPL_SHADOW_SOURCE="xrpl_ws"),
        source=injected,
    )

    health = initialize_xrpl_ingestion(app)

    assert health.reason == "INGESTION_READY"
    assert app.state.snapshot_source is injected
