import pytest

from app.config import Settings
from app.live.shadow_snapshot_source import StaticShadowSnapshotSource
from app.live.shadow_source_factory import build_shadow_source


def test_default_source_is_static_safe() -> None:
    source = build_shadow_source(Settings(_env_file=None))

    assert isinstance(source, StaticShadowSnapshotSource)
    assert source.next_snapshot() is None


def test_xrpl_ws_requires_explicit_injected_source() -> None:
    settings = Settings(_env_file=None, XRPL_SHADOW_SOURCE="xrpl_ws", XRPL_INGESTION_MODE="live_shadow")

    with pytest.raises(ValueError):
        build_shadow_source(settings)


def test_xrpl_ws_uses_injected_source_without_network_client() -> None:
    settings = Settings(_env_file=None, XRPL_SHADOW_SOURCE="xrpl_ws", XRPL_INGESTION_MODE="live_shadow")
    injected = StaticShadowSnapshotSource([])

    assert build_shadow_source(settings, injected_source=injected) is injected


def test_invalid_source_fails_closed() -> None:
    settings = Settings(_env_file=None, XRPL_SHADOW_SOURCE="bad")

    with pytest.raises(ValueError):
        build_shadow_source(settings)
