from datetime import datetime, timedelta, timezone

from app.calibration.liquidity_decay_analyzer import LiquidityDecayAnalyzer
from app.db.models import XRPLOrderbookSnapshot


def _snap(ledger: int, bid_depth: float, ask_depth: float, spread_pct: float, observed_at: datetime) -> XRPLOrderbookSnapshot:
    return XRPLOrderbookSnapshot(
        token_id=1,
        ledger_index=ledger,
        best_bid=1.0,
        best_ask=1.0 + (spread_pct / 100.0),
        bid_depth_xrp=bid_depth,
        ask_depth_xrp=ask_depth,
        spread_pct=spread_pct,
        levels_json=[],
        observed_at=observed_at,
    )


def test_stable_book_has_low_decay() -> None:
    now = datetime.now(tz=timezone.utc)
    snapshots = [
        _snap(100, 1000.0, 1000.0, 1.0, now),
        _snap(101, 995.0, 1002.0, 1.0, now + timedelta(seconds=4)),
        _snap(102, 1001.0, 998.0, 1.1, now + timedelta(seconds=8)),
    ]
    out = LiquidityDecayAnalyzer().analyze(snapshots)
    assert out.decay_score < 0.15
    assert out.collapse_events == 0


def test_shrinking_book_has_high_decay() -> None:
    now = datetime.now(tz=timezone.utc)
    snapshots = [
        _snap(200, 1000.0, 1000.0, 1.0, now),
        _snap(201, 600.0, 650.0, 2.5, now + timedelta(seconds=4)),
        _snap(202, 400.0, 420.0, 3.5, now + timedelta(seconds=8)),
    ]
    out = LiquidityDecayAnalyzer().analyze(snapshots)
    assert out.decay_score > 0.45
    assert out.depth_loss_rate > 0.25


def test_spoof_removal_triggers_collapse_event() -> None:
    now = datetime.now(tz=timezone.utc)
    snapshots = [
        _snap(300, 1200.0, 1200.0, 1.2, now),
        _snap(301, 500.0, 480.0, 2.8, now + timedelta(seconds=4)),
        _snap(302, 480.0, 470.0, 3.0, now + timedelta(seconds=8)),
    ]
    out = LiquidityDecayAnalyzer().analyze(snapshots)
    assert out.collapse_events >= 1
    assert out.level_removal_frequency > 0.0
