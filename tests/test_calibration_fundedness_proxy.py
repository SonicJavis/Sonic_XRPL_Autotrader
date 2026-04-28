from datetime import datetime, timedelta, timezone

from app.calibration.fundedness_proxy import FundednessProxy
from app.db.models import XRPLOrderbookSnapshot


def _snap(ledger: int, bid_depth: float, ask_depth: float, observed_at: datetime) -> XRPLOrderbookSnapshot:
    return XRPLOrderbookSnapshot(
        token_id=1,
        ledger_index=ledger,
        best_bid=1.0,
        best_ask=1.01,
        bid_depth_xrp=bid_depth,
        ask_depth_xrp=ask_depth,
        spread_pct=1.0,
        levels_json=[],
        observed_at=observed_at,
    )


def test_stable_book_has_high_fundedness_confidence() -> None:
    now = datetime.now(tz=timezone.utc)
    snapshots = [
        _snap(100, 500.0, 510.0, now),
        _snap(101, 505.0, 500.0, now + timedelta(seconds=4)),
        _snap(102, 498.0, 506.0, now + timedelta(seconds=8)),
    ]
    out = FundednessProxy().evaluate(snapshots)
    assert out.fundedness_confidence > 0.75


def test_flickering_walls_have_low_fundedness_confidence() -> None:
    now = datetime.now(tz=timezone.utc)
    snapshots = [
        _snap(200, 1200.0, 1200.0, now),
        _snap(201, 120.0, 110.0, now + timedelta(seconds=4)),
        _snap(202, 1250.0, 1260.0, now + timedelta(seconds=8)),
        _snap(203, 100.0, 90.0, now + timedelta(seconds=12)),
    ]
    out = FundednessProxy().evaluate(snapshots)
    assert out.fundedness_confidence < 0.45
    assert out.wall_flicker_rate > 0.0
