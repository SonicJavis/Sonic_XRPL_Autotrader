from __future__ import annotations

import json
from datetime import datetime, timezone
from math import isfinite

from fastapi import APIRouter, Request
from sqlmodel import select

from app.db.models import ShadowDecisionRecord
from app.feedback.shadow_decision_tracker import ShadowDecisionTracker

router = APIRouter()


def _meta() -> dict[str, object]:
    return {
        "is_live": True,
        "is_shadow": True,
        "is_executable": False,
        "is_advisory": True,
        "xrpl_warning": "Shadow decisions are advisory only; book_offers is snapshot-based and observed liquidity is not executable truth",
    }


def _safe_limit(raw: int) -> int:
    return min(max(int(raw), 1), 5000)


def _utc(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc).isoformat()


def _json_list(raw: str) -> list[str]:
    try:
        payload = json.loads(str(raw or "[]"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return sorted({str(item) for item in payload})


def _json_dict(raw: str) -> dict[str, object]:
    try:
        payload = json.loads(str(raw or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _finite(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return value if isfinite(value) else 0.0


def _row_to_dict(row: ShadowDecisionRecord) -> dict[str, object]:
    return {
        "id": int(row.id or 0),
        "token_id": int(row.token_id),
        "issuer": row.issuer,
        "currency": row.currency,
        "observed_at": _utc(row.observed_at),
        "ledger_index": int(row.ledger_index),
        "requested_size": _finite(row.requested_size),
        "latency_path_probability": _finite(row.latency_path_probability),
        "memory_adjusted_probability": _finite(row.memory_adjusted_probability),
        "effective_size": _finite(row.effective_size),
        "memory_adjusted_effective_size": _finite(row.memory_adjusted_effective_size),
        "uncertainty_adjusted_value": _finite(row.uncertainty_adjusted_value),
        "drift_adjusted_ev": _finite(row.drift_adjusted_ev),
        "regime": row.regime,
        "advisory_risk_level": row.advisory_risk_level,
        "risk_flags": _json_list(row.risk_flags_json),
        "calibration_snapshot": _json_dict(row.calibration_snapshot_json),
        "is_shadow": bool(row.is_shadow),
        "is_executable": bool(row.is_executable),
    }


def _load_rows(request: Request, *, limit: int) -> list[ShadowDecisionRecord]:
    container = request.app.state.container
    with container.session_factory() as session:
        return session.exec(
            select(ShadowDecisionRecord)
            .order_by(ShadowDecisionRecord.observed_at.desc(), ShadowDecisionRecord.id.desc())
            .limit(_safe_limit(limit))
        ).all()


@router.get("/live/shadow/decisions")
def live_shadow_decisions(request: Request, limit: int = 200) -> dict[str, object]:
    rows = _load_rows(request, limit=limit)
    return {
        **_meta(),
        "count": len(rows),
        "limit": _safe_limit(limit),
        "decisions": [_row_to_dict(row) for row in rows],
    }


@router.get("/live/shadow/summary")
def live_shadow_summary(request: Request, limit: int = 500) -> dict[str, object]:
    rows = _load_rows(request, limit=limit)
    summary = ShadowDecisionTracker().summarize(rows)
    return {
        **_meta(),
        "limit": _safe_limit(limit),
        "summary": summary.to_dict(),
    }
