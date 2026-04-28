from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sqlmodel import select

from app.calibration.recommendation_engine import ConfidenceWeightedCalibrationEngine, LiveCalibrationSample
from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot
from app.live.dashboard_metrics import LiveDashboardMetrics, build_live_dashboard_metrics

router = APIRouter()


def _base_response_meta() -> dict[str, object]:
    return {
        "is_live": True,
        "is_shadow": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": "Shadow-mode XRPL observation only; book_offers is snapshot-only and observed liquidity may not be executable",
    }


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _clamp(raw: float) -> float:
    return max(0.0, min(1.0, float(raw)))


def _execution_details(row: ExecutionRecord) -> dict[str, object]:
    try:
        return json.loads(str(row.execution_details_json or "{}"))
    except json.JSONDecodeError:
        return {}


def _is_shadow_execution(row: ExecutionRecord) -> bool:
    return bool(_execution_details(row).get("shadow"))


def _load_live_state(request: Request, *, execution_limit: int = 500, snapshot_limit: int = 1200) -> tuple[list[ExecutionRecord], list[XRPLOrderbookSnapshot]]:
    container = request.app.state.container
    with container.session_factory() as session:
        executions = session.exec(select(ExecutionRecord).order_by(ExecutionRecord.id.desc()).limit(execution_limit)).all()
        snapshots = session.exec(
            select(XRPLOrderbookSnapshot).order_by(XRPLOrderbookSnapshot.ledger_index.asc()).limit(snapshot_limit)
        ).all()
    return executions, snapshots


def _shadow_executions(executions: list[ExecutionRecord]) -> list[ExecutionRecord]:
    return [row for row in executions if _is_shadow_execution(row)]


def _build_live_samples(executions: list[ExecutionRecord]) -> list[LiveCalibrationSample]:
    samples: list[LiveCalibrationSample] = []
    for row in _shadow_executions(executions):
        details = _execution_details(row)
        requested_size = max(0.0, float(row.requested_size or 0.0))
        simulated_fill_ratio = 0.0 if requested_size <= 0 else _clamp(float(row.filled_size or 0.0) / requested_size)
        samples.append(
            LiveCalibrationSample(
                simulated_fill_ratio=simulated_fill_ratio,
                observed_fill_ratio=_clamp(float(details.get("observed_fill_ratio", simulated_fill_ratio))),
                disagreement_score=_clamp(float(details.get("disagreement_score", 0.0))),
                ledger_delay_error=_clamp(float(details.get("ledger_delay_error", 0.0))),
                path_execution_risk=_clamp(float(details.get("path_execution_risk", 0.0))),
                observation_confidence=_clamp(float(details.get("observation_confidence", 0.0))),
            )
        )
    return samples


def _false_confidence_rate_live(executions: list[ExecutionRecord]) -> float:
    shadow_rows = _shadow_executions(executions)
    if not shadow_rows:
        return 0.0
    flagged = 0
    for row in shadow_rows:
        if bool(_execution_details(row).get("false_confidence_flag", False)):
            flagged += 1
    return round(flagged / len(shadow_rows), 6)


def _observation_confidence_live(executions: list[ExecutionRecord]) -> float:
    shadow_rows = _shadow_executions(executions)
    if not shadow_rows:
        return 0.0
    values = [_clamp(float(_execution_details(row).get("observation_confidence", 0.0))) for row in shadow_rows]
    return round(sum(values) / len(values), 6)


def _route_confidence_live(executions: list[ExecutionRecord]) -> float:
    shadow_rows = _shadow_executions(executions)
    if not shadow_rows:
        return 0.0
    values = []
    for row in shadow_rows:
        details = _execution_details(row)
        if "route_confidence" in details:
            values.append(_clamp(float(details.get("route_confidence", 0.0))))
        else:
            values.append(round(1.0 - _clamp(float(details.get("path_execution_risk", 0.0))), 6))
    return round(sum(values) / len(values), 6)


def _latest_snapshot_at(orderbook_snapshots: list[XRPLOrderbookSnapshot]) -> str | None:
    if not orderbook_snapshots:
        return None
    latest = max(orderbook_snapshots, key=lambda row: _utc(row.observed_at))
    return _utc(latest.observed_at).isoformat()


def _live_metrics_payload(executions: list[ExecutionRecord], snapshots: list[XRPLOrderbookSnapshot]) -> tuple[LiveDashboardMetrics, dict[str, float]]:
    dashboard = build_live_dashboard_metrics(executions=executions, orderbook_snapshots=snapshots)
    live_summary = ConfidenceWeightedCalibrationEngine().summarize_live_metrics(_build_live_samples(executions))
    derived = {
        "live_simulated_fail_rate": live_summary.live_simulated_fail_rate,
        "path_mismatch_rate": live_summary.path_mismatch_rate,
        "ledger_delay_error": live_summary.ledger_delay_error,
        "false_confidence_rate_live": _false_confidence_rate_live(executions),
        "observation_confidence_live": _observation_confidence_live(executions),
        "route_confidence_live": _route_confidence_live(executions),
    }
    return dashboard, derived


@router.get("/live/status")
def live_status(request: Request) -> dict[str, object]:
    executions, snapshots = _load_live_state(request, execution_limit=300, snapshot_limit=500)
    dashboard, _ = _live_metrics_payload(executions, snapshots)
    return {
        **_base_response_meta(),
        "status": {
            "feed_status": "ACTIVE" if dashboard.latest_ledger_index > 0 else "IDLE",
            "latest_ledger_index": dashboard.latest_ledger_index,
            "ledger_gap_count": dashboard.ledger_gap_count,
            "snapshot_age_ms": dashboard.snapshot_age_ms,
            "snapshot_quality_score": dashboard.snapshot_quality_score,
            "shadow_execution_count": dashboard.shadow_execution_count,
            "latest_snapshot_at": _latest_snapshot_at(snapshots),
        },
    }


@router.get("/live/metrics")
def live_metrics(request: Request) -> dict[str, object]:
    executions, snapshots = _load_live_state(request)
    dashboard, derived = _live_metrics_payload(executions, snapshots)
    return {
        **_base_response_meta(),
        "metrics": {
            "latest_ledger_index": dashboard.latest_ledger_index,
            "ledger_gap_count": dashboard.ledger_gap_count,
            "snapshot_age_ms": dashboard.snapshot_age_ms,
            "snapshot_quality_score": dashboard.snapshot_quality_score,
            "shadow_execution_count": dashboard.shadow_execution_count,
            "shadow_fill_rate": dashboard.shadow_fill_rate,
            "disagreement_score_live": dashboard.live_disagreement_score,
            "path_execution_risk": dashboard.avg_path_execution_risk,
            "live_simulated_fail_rate": derived["live_simulated_fail_rate"],
            "path_mismatch_rate": derived["path_mismatch_rate"],
            "ledger_delay_error": derived["ledger_delay_error"],
            "observation_confidence_live": derived["observation_confidence_live"],
            "route_confidence_live": derived["route_confidence_live"],
        },
    }


@router.get("/live/executions")
def live_executions(request: Request, limit: int = 200) -> dict[str, object]:
    executions, _ = _load_live_state(request, execution_limit=min(max(limit, 1), 1000), snapshot_limit=50)
    shadow_rows = _shadow_executions(executions)
    rows = []
    for row in shadow_rows[:limit]:
        details = _execution_details(row)
        rows.append(
            {
                "execution_id": int(row.id or 0),
                "token_id": int(row.token_id),
                "signal_id": int(row.signal_id),
                "side": row.side,
                "requested_size": float(row.requested_size or 0.0),
                "filled_size": float(row.filled_size or 0.0),
                "fill_status": row.fill_status,
                "failure_reason": row.failure_reason,
                "entry_ledger": int(details.get("entry_ledger", row.ledger_index_snapshot or 0)),
                "execution_ledger": int(row.ledger_index_execution or 0),
                "inclusion_ledger": int(row.ledger_index_inclusion or 0),
                "snapshot_age_ms": int(row.snapshot_age_ms or 0),
                "disagreement_score": _clamp(float(details.get("disagreement_score", 0.0))),
                "observation_confidence": _clamp(float(details.get("observation_confidence", 0.0))),
                "path_execution_risk": _clamp(float(details.get("path_execution_risk", 0.0))),
                "route_confidence": (
                    _clamp(float(details.get("route_confidence", 0.0)))
                    if "route_confidence" in details
                    else round(1.0 - _clamp(float(details.get("path_execution_risk", 0.0))), 6)
                ),
                "mid_ledger_fills_disabled": bool(details.get("mid_ledger_fills_disabled", True)),
            }
        )
    return {**_base_response_meta(), "count": len(shadow_rows), "executions": rows}


@router.get("/live/uncertainty")
def live_uncertainty(request: Request) -> dict[str, object]:
    executions, snapshots = _load_live_state(request)
    dashboard, derived = _live_metrics_payload(executions, snapshots)
    return {
        **_base_response_meta(),
        "uncertainty": {
            "disagreement_score_live": dashboard.live_disagreement_score,
            "false_confidence_rate_live": derived["false_confidence_rate_live"],
            "observation_confidence_live": derived["observation_confidence_live"],
            "path_execution_risk": dashboard.avg_path_execution_risk,
            "route_confidence_live": derived["route_confidence_live"],
            "path_mismatch_rate": derived["path_mismatch_rate"],
            "ledger_delay_error": derived["ledger_delay_error"],
            "snapshot_quality_score": dashboard.snapshot_quality_score,
            "shadow_fill_rate": dashboard.shadow_fill_rate,
        },
        "sample_size": len(_shadow_executions(executions)),
    }