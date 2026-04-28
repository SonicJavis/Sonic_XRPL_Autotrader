from datetime import datetime, timedelta, timezone

from app.live.book_snapshot_engine import BookSnapshotDiff, PulledBookSnapshot
from app.live.orderbook_sequence_builder import OrderbookSequenceBuilder


def _snapshot(
    ledger_index: int,
    *,
    best_bid: float,
    best_ask: float,
    bid_depth_xrp: float,
    ask_depth_xrp: float,
    order_count: int,
    offer_count_delta: int = 0,
    liquidity_delta_xrp: float = 0.0,
) -> PulledBookSnapshot:
    return PulledBookSnapshot(
        token_key="USD.rIssuer",
        ledger_index=ledger_index,
        trigger="new_ledger",
        observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc) + timedelta(seconds=ledger_index),
        snapshot_age_ms=0,
        possibly_stale=False,
        best_bid=best_bid,
        best_ask=best_ask,
        bid_depth_xrp=bid_depth_xrp,
        ask_depth_xrp=ask_depth_xrp,
        liquidity_xrp=bid_depth_xrp + ask_depth_xrp,
        order_count=order_count,
        raw_offer_count=order_count,
        valid=True,
        diff=BookSnapshotDiff(
            best_bid_changed=True,
            best_ask_changed=True,
            bid_depth_delta_xrp=0.0,
            ask_depth_delta_xrp=0.0,
            liquidity_delta_xrp=liquidity_delta_xrp,
            offer_count_delta=offer_count_delta,
        ),
    )


def test_orderbook_sequence_builder_measures_persistence_and_churn() -> None:
    builder = OrderbookSequenceBuilder()
    result = builder.build(
        token_id=1,
        pulled_snapshots=[
            _snapshot(100, best_bid=0.99, best_ask=1.01, bid_depth_xrp=500.0, ask_depth_xrp=480.0, order_count=8),
            _snapshot(101, best_bid=0.98, best_ask=1.03, bid_depth_xrp=320.0, ask_depth_xrp=280.0, order_count=7, offer_count_delta=-1, liquidity_delta_xrp=-380.0),
            _snapshot(103, best_bid=0.96, best_ask=1.06, bid_depth_xrp=120.0, ask_depth_xrp=110.0, order_count=4, offer_count_delta=-3, liquidity_delta_xrp=-370.0),
        ],
    )

    assert result.sequence.start_ledger == 100
    assert result.sequence.end_ledger == 103
    assert result.depth_persistence < 1.0
    assert result.top_of_book_churn == 1.0
    assert result.liquidity_disappearance_rate >= 0.5
    assert result.missing_ledgers == 1
    assert "disappearing_liquidity" in result.warnings
    assert "missing_ledgers" in result.warnings


def test_orderbook_sequence_builder_flags_fake_walls_and_flicker() -> None:
    builder = OrderbookSequenceBuilder()
    result = builder.build(
        token_id=1,
        pulled_snapshots=[
            _snapshot(200, best_bid=0.99, best_ask=1.01, bid_depth_xrp=450.0, ask_depth_xrp=500.0, order_count=10),
            _snapshot(201, best_bid=0.99, best_ask=1.01, bid_depth_xrp=430.0, ask_depth_xrp=120.0, order_count=6, offer_count_delta=-4, liquidity_delta_xrp=-400.0),
            _snapshot(202, best_bid=1.00, best_ask=1.04, bid_depth_xrp=460.0, ask_depth_xrp=520.0, order_count=11, offer_count_delta=5, liquidity_delta_xrp=430.0),
        ],
    )

    assert result.fake_wall_risk > 0.0
    assert result.flicker_risk > 0.0
    assert "fake_walls" in result.warnings
    assert "flicker" in result.warnings