import json
from datetime import datetime, timedelta, timezone

from app.db.models import XRPLOrderbookSnapshot
from app.live.shadow_execution_loop import ShadowExecutionLoop, ShadowExecutionRequest


def _snapshot(ledger: int, *, ask_depth: float, best_ask: float, observed_at: datetime) -> XRPLOrderbookSnapshot:
    return XRPLOrderbookSnapshot(
        token_id=1,
        ledger_index=ledger,
        best_bid=max(0.000001, best_ask - 0.02),
        best_ask=best_ask,
        bid_depth_xrp=max(0.0, ask_depth * 0.8),
        ask_depth_xrp=ask_depth,
        spread_pct=2.0,
        observed_at=observed_at,
    )


def test_shadow_execution_waits_for_next_ledger_close() -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    loop = ShadowExecutionLoop()
    record = loop.simulate(
        ShadowExecutionRequest(
            token_id=1,
            signal_id=10,
            side="BUY",
            requested_size_xrp=100.0,
            entry_ledger=500,
            snapshots=[
                _snapshot(500, ask_depth=400.0, best_ask=1.01, observed_at=now),
                _snapshot(501, ask_depth=220.0, best_ask=1.02, observed_at=now + timedelta(seconds=4)),
            ],
        )
    )

    details = json.loads(record.execution_details_json)
    assert record.ledger_index_snapshot == 500
    assert record.ledger_index_execution == 501
    assert record.filled_size > 0.0
    assert details["mid_ledger_fills_disabled"] is True


def test_shadow_execution_uses_future_ledgers_only_and_can_partial_fill() -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    loop = ShadowExecutionLoop()
    record = loop.simulate(
        ShadowExecutionRequest(
            token_id=1,
            signal_id=11,
            side="BUY",
            requested_size_xrp=300.0,
            entry_ledger=700,
            snapshots=[
                _snapshot(700, ask_depth=800.0, best_ask=1.01, observed_at=now),
                _snapshot(701, ask_depth=0.0, best_ask=1.03, observed_at=now + timedelta(seconds=4)),
                _snapshot(702, ask_depth=200.0, best_ask=1.05, observed_at=now + timedelta(seconds=8)),
            ],
        )
    )

    assert record.ledger_index_execution == 702
    assert record.fill_status == "PARTIAL"
    assert record.filled_size == 130.0


def test_shadow_execution_fails_closed_when_no_future_ledger_has_depth() -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    loop = ShadowExecutionLoop()
    record = loop.simulate(
        ShadowExecutionRequest(
            token_id=1,
            signal_id=12,
            side="BUY",
            requested_size_xrp=90.0,
            entry_ledger=900,
            snapshots=[
                _snapshot(900, ask_depth=500.0, best_ask=1.01, observed_at=now),
                _snapshot(901, ask_depth=0.0, best_ask=1.04, observed_at=now + timedelta(seconds=4)),
                _snapshot(902, ask_depth=0.0, best_ask=1.06, observed_at=now + timedelta(seconds=8)),
            ],
        )
    )

    assert record.fill_status == "UNFILLED"
    assert record.failure_reason == "NO_ELIGIBLE_LEDGER_CLOSE"
    assert record.ledger_index_execution == 902