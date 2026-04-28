from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


@dataclass(slots=True)
class LiveDashboardMetrics:
    latest_ledger_index: int
    ledger_gap_count: int
    snapshot_age_ms: int
    snapshot_quality_score: float
    shadow_execution_count: int
    shadow_fill_rate: float
    live_disagreement_score: float
    avg_path_execution_risk: float


def build_live_dashboard_metrics(
    *,
    executions: list[ExecutionRecord],
    orderbook_snapshots: list[XRPLOrderbookSnapshot],
    now: datetime | None = None,
) -> LiveDashboardMetrics:
    now_utc = _utc(now or datetime.now(tz=timezone.utc))
    ordered_snapshots = sorted(orderbook_snapshots, key=lambda row: int(row.ledger_index))

    latest_ledger_index = int(ordered_snapshots[-1].ledger_index) if ordered_snapshots else 0
    ledger_gap_count = 0
    quality_components: list[float] = []
    snapshot_age_ms = 0

    if ordered_snapshots:
        latest_snapshot = max(ordered_snapshots, key=lambda row: _utc(row.observed_at))
        snapshot_age_ms = max(0, int((now_utc - _utc(latest_snapshot.observed_at)).total_seconds() * 1000.0))
        for prev, curr in zip(ordered_snapshots[:-1], ordered_snapshots[1:]):
            ledger_gap_count += max(0, int(curr.ledger_index) - int(prev.ledger_index) - 1)
        for row in ordered_snapshots[-25:]:
            spread_quality = max(0.0, min(1.0, 1.0 - (float(row.spread_pct) / 8.0)))
            depth_total = max(0.0, float(row.bid_depth_xrp) + float(row.ask_depth_xrp))
            depth_quality = max(0.0, min(1.0, depth_total / 800.0))
            quality_components.append((spread_quality * 0.45) + (depth_quality * 0.55))

    shadow_details: list[dict[str, float | bool]] = []
    for row in executions:
        try:
            details = json.loads(str(row.execution_details_json or "{}"))
        except json.JSONDecodeError:
            details = {}
        if bool(details.get("shadow")):
            shadow_details.append(details)

    shadow_execution_count = len(shadow_details)
    shadow_fill_rate = 0.0
    live_disagreement_score = 0.0
    avg_path_execution_risk = 0.0
    if shadow_execution_count > 0:
        shadow_rows = [row for row in executions if _is_shadow_execution(row)]
        shadow_fill_rate = sum(1 for row in shadow_rows if str(row.fill_status) in {"FILLED", "PARTIAL"}) / shadow_execution_count
        live_disagreement_score = sum(float(details.get("disagreement_score", 0.0)) for details in shadow_details) / shadow_execution_count
        avg_path_execution_risk = sum(float(details.get("path_execution_risk", 0.0)) for details in shadow_details) / shadow_execution_count

    snapshot_quality_score = 0.0 if not quality_components else sum(quality_components) / len(quality_components)
    return LiveDashboardMetrics(
        latest_ledger_index=latest_ledger_index,
        ledger_gap_count=ledger_gap_count,
        snapshot_age_ms=snapshot_age_ms,
        snapshot_quality_score=round(snapshot_quality_score, 6),
        shadow_execution_count=shadow_execution_count,
        shadow_fill_rate=round(shadow_fill_rate, 6),
        live_disagreement_score=round(live_disagreement_score, 6),
        avg_path_execution_risk=round(avg_path_execution_risk, 6),
    )


def _is_shadow_execution(row: ExecutionRecord) -> bool:
    try:
        details = json.loads(str(row.execution_details_json or "{}"))
    except json.JSONDecodeError:
        return False
    return bool(details.get("shadow"))