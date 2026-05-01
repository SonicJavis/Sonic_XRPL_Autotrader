from __future__ import annotations

from time import monotonic

from fastapi import APIRouter, Request

router = APIRouter()
STARTED_AT = monotonic()


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    container = request.app.state.container
    profile = getattr(request.app.state, "runtime_profile", None)
    xrpl_health = {"ok": True, "reason": "SKIPPED_IN_PRODUCTION"}
    if profile is None or getattr(profile, "mode", "LOCAL_DEV") != "PRODUCTION":
        xrpl_health = container.xrpl_client.health_check()
    return {
        "status": "ok",
        "mode": getattr(profile, "mode", "LOCAL_DEV"),
        "validated_data_only": True,
        "is_executable": False,
        "is_shadow": True,
        "is_advisory": True,
        "xrpl": xrpl_health,
    }


@router.get("/metrics")
def metrics(request: Request) -> dict[str, object]:
    settings = request.app.state.container.settings
    ingestion = getattr(request.app.state, "ingestion_adapter", None) or getattr(request.app.state, "xrpl_ingestion_adapter", None)
    health = ingestion.health().to_dict() if ingestion is not None and hasattr(ingestion, "health") else {}
    return {
        "uptime_seconds": round(max(0.0, monotonic() - STARTED_AT), 6),
        "mode": getattr(getattr(request.app.state, "runtime_profile", None), "mode", "LOCAL_DEV"),
        "ingestion_enabled": bool(settings.XRPL_INGESTION_ENABLED),
        "latest_validated_ledger_index": int(health.get("latest_validated_ledger_index", 0) or 0),
        "decay_staleness_summary": {
            "validated_data_only": True,
            "liquidity_decay_model": "ledger_first",
        },
        "gap_count": int(health.get("ledger_gap_count", health.get("stale_snapshot_count", 0)) or 0),
        "latency_summary": {
            "last_latency_ms": float(health.get("last_snapshot_latency_ms", 0.0) or 0.0),
            "backoff_seconds": float(health.get("backoff_seconds", 0.0) or 0.0),
        },
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
    }
