from datetime import datetime, timedelta, timezone

from app.config import Settings
from app.db.models import MarketSnapshot
from app.execution.liquidity_decay import analyze_liquidity_decay


def _snap(liquidity_xrp: float, seconds_ago: int) -> MarketSnapshot:
    return MarketSnapshot(
        token_id=1,
        price_xrp=1.0,
        liquidity_xrp=liquidity_xrp,
        liquidity_bid_xrp=liquidity_xrp / 2.0,
        liquidity_ask_xrp=liquidity_xrp / 2.0,
        spread_pct=0.5,
        best_bid=0.99,
        best_ask=1.01,
        bid_count=3,
        ask_count=3,
        created_at=datetime.now(tz=timezone.utc) - timedelta(seconds=seconds_ago),
    )


def test_collapse_triggers_reject_flags() -> None:
    settings = Settings(MIN_LIQUIDITY_XRP=100.0, MAX_TRADE_XRP=5.0)
    history = [_snap(1000.0, 5), _snap(950.0, 4), _snap(900.0, 3)]
    out = analyze_liquidity_decay(
        settings=settings,
        history=history,
        bids=[{"price": 1.0, "token_amount": 20.0, "xrp_value": 20.0}],
        asks=[{"price": 1.01, "token_amount": 20.0, "xrp_value": 20.2}],
        spread_pct=0.5,
    )
    assert out["collapse_flag"] is True


def test_spoof_triggers_reject_flags() -> None:
    settings = Settings(MIN_LIQUIDITY_XRP=100.0, MAX_TRADE_XRP=10.0)
    history = [_snap(300.0, 5), _snap(320.0, 4), _snap(310.0, 3)]
    out = analyze_liquidity_decay(
        settings=settings,
        history=history,
        bids=[{"price": 1.0, "token_amount": 1000.0, "xrp_value": 1000.0}, {"price": 0.99, "token_amount": 2.0, "xrp_value": 1.98}],
        asks=[{"price": 1.01, "token_amount": 3.0, "xrp_value": 3.03}, {"price": 1.02, "token_amount": 2.0, "xrp_value": 2.04}],
        spread_pct=0.4,
    )
    assert out["spoof_flag"] is True


def test_stable_book_passes_flags() -> None:
    settings = Settings(MIN_LIQUIDITY_XRP=100.0, MAX_TRADE_XRP=5.0)
    history = [_snap(300.0, 5), _snap(310.0, 4), _snap(290.0, 3)]
    out = analyze_liquidity_decay(
        settings=settings,
        history=history,
        bids=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}, {"price": 0.99, "token_amount": 80.0, "xrp_value": 79.2}],
        asks=[{"price": 1.01, "token_amount": 95.0, "xrp_value": 95.95}, {"price": 1.02, "token_amount": 85.0, "xrp_value": 86.7}],
        spread_pct=0.8,
    )
    assert out["collapse_flag"] is False
    assert out["spoof_flag"] is False
    assert out["fake_spread_flag"] is False
