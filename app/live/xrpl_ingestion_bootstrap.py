from __future__ import annotations

from app.config import Settings
from app.live.shadow_source_factory import build_shadow_source
from app.live.xrpl_ingestion_models import XRPLIngestionHealth


VALID_MODES = {"disabled", "replay", "live_shadow"}
VALID_SOURCES = {"static", "replay", "xrpl_ws"}


def initialize_xrpl_ingestion(app) -> XRPLIngestionHealth:
    settings: Settings = app.state.container.settings
    injected_source = getattr(app.state, "snapshot_source", None)
    app.state.ingestion_adapter = None
    app.state.xrpl_ingestion_adapter = None
    app.state.snapshot_source = None
    app.state.ingestion_mode = "disabled"
    mode = str(settings.XRPL_INGESTION_MODE).lower()
    source = str(settings.XRPL_SHADOW_SOURCE).lower()
    if not bool(settings.XRPL_INGESTION_ENABLED):
        return XRPLIngestionHealth(reason="INGESTION_DISABLED", ingestion_enabled=False, ingestion_mode="disabled", ingestion_source=source)
    if mode not in VALID_MODES or source not in VALID_SOURCES or mode == "disabled":
        return XRPLIngestionHealth(reason="INGESTION_INVALID_CONFIG", ingestion_enabled=False, ingestion_mode="disabled", ingestion_source=source)
    try:
        snapshot_source = build_shadow_source(settings, injected_source=injected_source if source == "xrpl_ws" else None)
    except ValueError:
        return XRPLIngestionHealth(reason="INGESTION_SOURCE_UNAVAILABLE", ingestion_enabled=False, ingestion_mode="disabled", ingestion_source=source)
    app.state.snapshot_source = snapshot_source
    app.state.ingestion_mode = mode
    app.state.ingestion_adapter = snapshot_source
    app.state.xrpl_ingestion_adapter = snapshot_source
    return XRPLIngestionHealth(
        connected=False,
        reason="INGESTION_READY",
        ingestion_enabled=True,
        ingestion_mode=mode,
        ingestion_source=source,
    )
