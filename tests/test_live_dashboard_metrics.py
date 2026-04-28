import json
from datetime import datetime, timedelta, timezone

from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot
from app.live.dashboard_metrics import build_live_dashboard_metrics


def _execution(*, shadow: bool, fill_status: str, disagreement_score: float, path_execution_risk: float) -> ExecutionRecord:
    return ExecutionRecord(
        token_id=1,
        signal_id=1,
        snapshot_id=1,
        side="BUY",
        requested_size=100.0,
        filled_size=60.0 if fill_status != "UNFILLED" else 0.0,
        fill_status=fill_status,
        execution_details_json=json.dumps(
            {
                "shadow": shadow,
                "disagreement_score": disagreement_score,
                "path_execution_risk": path_execution_risk,
            }
        ),
    )


def test_live_dashboard_metrics_summarize_shadow_and_snapshot_state() -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    metrics = build_live_dashboard_metrics(
        executions=[
            _execution(shadow=True, fill_status="PARTIAL", disagreement_score=0.7, path_execution_risk=0.8),
            _execution(shadow=True, fill_status="UNFILLED", disagreement_score=0.5, path_execution_risk=0.6),
            _execution(shadow=False, fill_status="FILLED", disagreement_score=0.1, path_execution_risk=0.1),
        ],
        orderbook_snapshots=[
            XRPLOrderbookSnapshot(token_id=1, ledger_index=100, best_bid=0.99, best_ask=1.01, bid_depth_xrp=300.0, ask_depth_xrp=280.0, spread_pct=2.0, observed_at=now - timedelta(seconds=8)),
            XRPLOrderbookSnapshot(token_id=1, ledger_index=102, best_bid=0.98, best_ask=1.03, bid_depth_xrp=220.0, ask_depth_xrp=210.0, spread_pct=3.0, observed_at=now - timedelta(seconds=4)),
        ],
        now=now,
    )

    assert metrics.latest_ledger_index == 102
    assert metrics.ledger_gap_count == 1
    assert metrics.snapshot_age_ms == 4000
    assert metrics.shadow_execution_count == 2
    assert metrics.shadow_fill_rate == 0.5
    assert metrics.live_disagreement_score == 0.6
    assert metrics.avg_path_execution_risk == 0.7
    assert metrics.snapshot_quality_score > 0.0