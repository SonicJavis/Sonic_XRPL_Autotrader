from __future__ import annotations

from app.config import Settings
from app.live.replay_snapshot_source import ReplaySnapshotSource
from app.live.shadow_snapshot_source import StaticShadowSnapshotSource, ShadowSnapshotSource


def build_shadow_source(settings: Settings, *, injected_source: ShadowSnapshotSource | None = None) -> ShadowSnapshotSource:
    source = str(settings.XRPL_SHADOW_SOURCE).lower()
    mode = str(settings.XRPL_INGESTION_MODE).lower()
    if source == "static":
        return StaticShadowSnapshotSource([])
    if source == "replay" or mode == "replay":
        return ReplaySnapshotSource()
    if source == "xrpl_ws":
        if injected_source is not None:
            return injected_source
        raise ValueError("xrpl_ws source requires explicit injected adapters")
    raise ValueError(f"unknown shadow source: {settings.XRPL_SHADOW_SOURCE}")
