from datetime import datetime, timedelta, timezone

from app.calibration.temporal_comparison import compare_simulation_vs_sequence
from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot


def _snapshot(ledger: int, ask_depth_xrp: float, spread_pct: float, ts: datetime) -> XRPLOrderbookSnapshot:
    return XRPLOrderbookSnapshot(
        token_id=1,
        ledger_index=ledger,
        best_bid=1.0,
        best_ask=1.0 + spread_pct / 100.0,
        bid_depth_xrp=ask_depth_xrp,
        ask_depth_xrp=ask_depth_xrp,
        spread_pct=spread_pct,
        levels_json=[],
        observed_at=ts,
    )


def _execution(requested: float, filled: float, slippage: float, snap_ledger: int, incl_ledger: int) -> ExecutionRecord:
    return ExecutionRecord(
        token_id=1,
        signal_id=1,
        snapshot_id=1,
        side="BUY",
        requested_size=requested,
        filled_size=filled,
        fill_status="FILLED" if filled >= requested else "PARTIAL",
        avg_fill_price=1.0,
        slippage_vs_top=slippage,
        snapshot_time=datetime.now(tz=timezone.utc),
        signal_time=datetime.now(tz=timezone.utc),
        execution_time=datetime.now(tz=timezone.utc),
        ledger_index_snapshot=snap_ledger,
        ledger_index_signal=snap_ledger,
        ledger_index_execution=snap_ledger + 1,
        ledger_index_inclusion=incl_ledger,
    )


def test_stable_sequence_has_low_temporal_error() -> None:
    now = datetime.now(tz=timezone.utc)
    seq = [
        _snapshot(100, 1000.0, 1.0, now),
        _snapshot(101, 980.0, 1.1, now + timedelta(seconds=4)),
        _snapshot(102, 970.0, 1.1, now + timedelta(seconds=8)),
    ]
    out = compare_simulation_vs_sequence(
        execution=_execution(100.0, 95.0, 0.5, 100, 102),
        sequence=seq,
    )
    assert out.execution_survivability_error < 0.15
    assert out.depth_overestimation < 0.05


def test_decaying_sequence_has_high_temporal_error() -> None:
    now = datetime.now(tz=timezone.utc)
    seq = [
        _snapshot(200, 1000.0, 1.0, now),
        _snapshot(201, 500.0, 2.5, now + timedelta(seconds=4)),
        _snapshot(202, 200.0, 3.5, now + timedelta(seconds=8)),
    ]
    out = compare_simulation_vs_sequence(
        execution=_execution(300.0, 290.0, 0.2, 200, 204),
        sequence=seq,
    )
    assert out.execution_survivability_error > 0.25
    assert out.slippage_underestimation > 0.0
    assert out.depth_overestimation > 0.5
