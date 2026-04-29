from __future__ import annotations

from fastapi import APIRouter, Request

from app.live.xrpl_ingestion_models import XRPLIngestionHealth

router = APIRouter()


@router.get("/live/ingestion/status")
def live_ingestion_status(request: Request) -> dict[str, object]:
    settings = request.app.state.container.settings
    adapter = getattr(request.app.state, "ingestion_adapter", None) or getattr(request.app.state, "xrpl_ingestion_adapter", None)
    if adapter is None:
        return XRPLIngestionHealth(
            reason="INGESTION_NOT_CONFIGURED",
            ingestion_enabled=bool(settings.XRPL_INGESTION_ENABLED),
            ingestion_mode=str(settings.XRPL_INGESTION_MODE),
            ingestion_source=str(settings.XRPL_SHADOW_SOURCE),
        ).to_dict()
    health = adapter.health()
    if isinstance(health, XRPLIngestionHealth):
        body = health.to_dict()
        body["ingestion_enabled"] = bool(settings.XRPL_INGESTION_ENABLED)
        body["ingestion_mode"] = str(getattr(request.app.state, "ingestion_mode", settings.XRPL_INGESTION_MODE))
        body["ingestion_source"] = str(settings.XRPL_SHADOW_SOURCE)
        body["is_executable"] = False
        return body
    if isinstance(health, dict):
        return {
            **XRPLIngestionHealth(
                ingestion_enabled=bool(settings.XRPL_INGESTION_ENABLED),
                ingestion_mode=str(settings.XRPL_INGESTION_MODE),
                ingestion_source=str(settings.XRPL_SHADOW_SOURCE),
            ).to_dict(),
            **health,
            "is_executable": False,
            "is_shadow": True,
            "is_advisory": True,
        }
    return XRPLIngestionHealth(
        reason="INGESTION_HEALTH_UNAVAILABLE",
        ingestion_enabled=bool(settings.XRPL_INGESTION_ENABLED),
        ingestion_mode=str(settings.XRPL_INGESTION_MODE),
        ingestion_source=str(settings.XRPL_SHADOW_SOURCE),
    ).to_dict()
