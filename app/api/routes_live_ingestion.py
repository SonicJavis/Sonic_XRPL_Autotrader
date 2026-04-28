from __future__ import annotations

from fastapi import APIRouter, Request

from app.live.xrpl_ingestion_models import XRPLIngestionHealth

router = APIRouter()


@router.get("/live/ingestion/status")
def live_ingestion_status(request: Request) -> dict[str, object]:
    adapter = getattr(request.app.state, "xrpl_ingestion_adapter", None)
    if adapter is None:
        return XRPLIngestionHealth(reason="INGESTION_NOT_CONFIGURED").to_dict()
    health = adapter.health()
    if isinstance(health, XRPLIngestionHealth):
        return health.to_dict()
    if isinstance(health, dict):
        return {**XRPLIngestionHealth().to_dict(), **health, "is_executable": False, "is_shadow": True, "is_advisory": True}
    return XRPLIngestionHealth(reason="INGESTION_HEALTH_UNAVAILABLE").to_dict()
