from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

from app.calibration.time_series import build_sequence
from app.db.models import XRPLOrderbookSequence, XRPLOrderbookSnapshot
from app.db.session import engine, init_db


def reset_tables() -> None:
    XRPLOrderbookSequence.__table__.drop(engine, checkfirst=True)
    XRPLOrderbookSnapshot.__table__.drop(engine, checkfirst=True)
    init_db()


def _snapshot(token_id: int, ledger: int, bid_depth: float, ask_depth: float, spread: float, observed_at: datetime) -> XRPLOrderbookSnapshot:
    return XRPLOrderbookSnapshot(
        token_id=token_id,
        ledger_index=ledger,
        best_bid=1.0,
        best_ask=1.0 + (spread / 100.0),
        bid_depth_xrp=bid_depth,
        ask_depth_xrp=ask_depth,
        spread_pct=spread,
        levels_json=[{"side": "bid", "xrp": bid_depth}, {"side": "ask", "xrp": ask_depth}],
        observed_at=observed_at,
    )


def test_sequence_builds_from_snapshots() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    snapshots = [
        _snapshot(1, 100, 500.0, 450.0, 1.0, now),
        _snapshot(1, 101, 480.0, 430.0, 1.2, now + timedelta(seconds=4)),
        _snapshot(1, 102, 470.0, 420.0, 1.4, now + timedelta(seconds=8)),
    ]

    seq = build_sequence(1, snapshots)
    assert seq.start_ledger == 100
    assert seq.end_ledger == 102
    assert seq.snapshot_count == 3
    assert seq.duration_ms == 8000


def test_sequence_enforces_ledger_ordering() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    snapshots = [
        _snapshot(1, 100, 500.0, 450.0, 1.0, now),
        _snapshot(1, 100, 490.0, 440.0, 1.1, now + timedelta(seconds=4)),
    ]
    with pytest.raises(ValueError, match="INVALID_LEDGER_ORDERING"):
        build_sequence(1, snapshots)


def test_sequence_metrics_computed() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    snapshots = [
        _snapshot(1, 200, 1000.0, 1000.0, 1.0, now),
        _snapshot(1, 201, 550.0, 550.0, 2.5, now + timedelta(seconds=4)),
        _snapshot(1, 202, 600.0, 550.0, 3.0, now + timedelta(seconds=8)),
    ]

    seq = build_sequence(1, snapshots)
    assert seq.decay_score > 0.0
    assert seq.volatility_score > 0.0
    assert seq.collapse_events >= 1

    with Session(engine) as session:
        session.add(seq)
        session.commit()
        assert session.get(XRPLOrderbookSequence, seq.id) is not None
