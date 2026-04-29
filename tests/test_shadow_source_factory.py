from app.config import Settings
from app.live.replay_snapshot_source import ReplaySnapshotSource
from app.live.shadow_snapshot_source import StaticShadowSnapshotSource
from app.live.shadow_source_factory import build_shadow_source


def test_source_factory_static() -> None:
    settings = Settings(XRPL_SHADOW_SOURCE="static")

    assert isinstance(build_shadow_source(settings), StaticShadowSnapshotSource)


def test_source_factory_replay() -> None:
    settings = Settings(XRPL_INGESTION_MODE="replay", XRPL_SHADOW_SOURCE="replay")

    assert isinstance(build_shadow_source(settings), ReplaySnapshotSource)


def test_source_factory_invalid_fails_closed() -> None:
    settings = Settings(XRPL_SHADOW_SOURCE="bad")

    try:
        build_shadow_source(settings)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid source should fail closed")
