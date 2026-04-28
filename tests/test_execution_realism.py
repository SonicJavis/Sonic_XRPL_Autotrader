from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlmodel import Session, select

from app.alpha.engine import AlphaEngine
from app.config import Settings
from app.db.models import (
    AlphaCooldownRecord,
    AlphaSignal,
    CapitalLedger,
    CapitalReservation,
    ExecutionRecord,
    MarketDepthLevel,
    MarketSnapshot,
    PaperTrade,
    PaperTradeOutcome,
    Position,
    PositionExitFill,
    RiskDecisionRecord,
    RiskEvent,
    Signal,
    WatchedToken,
)
from app.db.session import engine, init_db
from app.execution.fill_simulator import simulate_entry_buy, simulate_exit_sell, validate_orderbook
from app.execution.paper import PaperExecutor
from app.execution.pipeline import ExecutionPipeline
from app.risk.kill_switch import KillSwitch
from app.risk.risk_manager import RiskManager
from app.strategies.new_token_scanner import NewTokenScannerStrategy
from app.strategies.strategy_registry import StrategyRegistry


class FakeXRPLClient:
    def get_book_offers(self, taker_gets, taker_pays):
        if isinstance(taker_gets, str):
            return {
                "offers": [
                    {"quality": 0.99, "taker_gets": 990.0, "taker_pays": 1000.0},
                    {"quality": 0.98, "taker_gets": 980.0, "taker_pays": 1000.0},
                    {"quality": 0.97, "taker_gets": 970.0, "taker_pays": 1000.0},
                ]
            }
        return {
            "offers": [
                {"quality": 1.01, "taker_gets": 1000.0, "taker_pays": 1010.0},
                {"quality": 1.02, "taker_gets": 1000.0, "taker_pays": 1020.0},
                {"quality": 1.03, "taker_gets": 1000.0, "taker_pays": 1030.0},
            ]
        }


def reset_tables() -> None:
    CapitalReservation.__table__.drop(engine, checkfirst=True)
    CapitalLedger.__table__.drop(engine, checkfirst=True)
    PaperTrade.__table__.drop(engine, checkfirst=True)
    PositionExitFill.__table__.drop(engine, checkfirst=True)
    ExecutionRecord.__table__.drop(engine, checkfirst=True)
    Position.__table__.drop(engine, checkfirst=True)
    PaperTradeOutcome.__table__.drop(engine, checkfirst=True)
    AlphaCooldownRecord.__table__.drop(engine, checkfirst=True)
    MarketDepthLevel.__table__.drop(engine, checkfirst=True)
    AlphaSignal.__table__.drop(engine, checkfirst=True)
    RiskDecisionRecord.__table__.drop(engine, checkfirst=True)
    Signal.__table__.drop(engine, checkfirst=True)
    RiskEvent.__table__.drop(engine, checkfirst=True)
    MarketSnapshot.__table__.drop(engine, checkfirst=True)
    WatchedToken.__table__.drop(engine, checkfirst=True)
    init_db()


def build_pipeline(settings: Settings) -> ExecutionPipeline:
    registry = StrategyRegistry()
    registry.register(NewTokenScannerStrategy(settings=settings))
    risk = RiskManager(settings, KillSwitch())
    paper = PaperExecutor(settings)
    alpha = AlphaEngine(settings)
    return ExecutionPipeline(settings, FakeXRPLClient(), registry, risk, paper, alpha)


def test_no_midpoint_fills() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[
            {"price": 1.01, "token_amount": 1000.0, "xrp_value": 1010.0},
            {"price": 1.02, "token_amount": 1000.0, "xrp_value": 1020.0},
        ],
        best_bid=0.99,
        best_ask=1.01,
        requested_size_xrp=1200.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    mid = (0.99 + 1.01) / 2.0
    assert out.avg_entry_price is not None
    assert out.avg_entry_price != pytest.approx(mid)


def test_partial_fill_behavior() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=200.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.fill_status == "PARTIAL"
    assert out.filled_size < out.requested_size


def test_no_liquidity_failure_reason() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[],
        best_bid=0.0,
        best_ask=0.0,
        requested_size_xrp=50.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.fill_status == "UNFILLED"
    assert out.failure_reason in {"INVALID_ORDERBOOK", "NO_LIQUIDITY"}


def test_stale_snapshot_rejection() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=10.0,
        snapshot_time=now - timedelta(seconds=5),
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.failure_reason == "STALE_MARKET_DATA"


def test_staged_latency_longer_delay_reduces_fill_size() -> None:
    now = datetime.now(tz=timezone.utc)
    fast = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=85.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        snapshot_to_decision_ms=20,
        decision_to_submission_ms=20,
        submission_to_inclusion_ms=20,
        max_snapshot_age_ms=5000,
        liquidity_haircut_pct=0.0,
        latency_haircut_pct=0.0,
    )
    slow = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=85.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        snapshot_to_decision_ms=3000,
        decision_to_submission_ms=3000,
        submission_to_inclusion_ms=3000,
        max_snapshot_age_ms=10000,
        liquidity_haircut_pct=0.0,
        latency_haircut_pct=0.0,
    )
    assert slow.filled_size < fast.filled_size


def test_staged_latency_stale_rejection() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=10.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        snapshot_to_decision_ms=1000,
        decision_to_submission_ms=1000,
        submission_to_inclusion_ms=1000,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.failure_reason == "STALE_MARKET_DATA"


def test_total_latency_equals_staged_sum() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=10.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        snapshot_to_decision_ms=111,
        decision_to_submission_ms=222,
        submission_to_inclusion_ms=333,
        max_snapshot_age_ms=5000,
        liquidity_haircut_pct=0.0,
    )
    assert out.total_execution_latency_ms == 666
    assert out.execution_latency_ms == 666


def test_drift_window_reduces_fillable_liquidity() -> None:
    now = datetime.now(tz=timezone.utc)
    baseline = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 50.0, "xrp_value": 50.0},
            {"price": 1.01, "token_amount": 50.0, "xrp_value": 50.5},
            {"price": 1.02, "token_amount": 50.0, "xrp_value": 51.0},
        ],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=120.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=5000,
        liquidity_haircut_pct=0.0,
        execution_window_snapshots=0,
    )
    drifted = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 50.0, "xrp_value": 50.0},
            {"price": 1.01, "token_amount": 50.0, "xrp_value": 50.5},
            {"price": 1.02, "token_amount": 50.0, "xrp_value": 51.0},
        ],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=120.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=5000,
        liquidity_haircut_pct=0.0,
        execution_window_snapshots=3,
    )
    assert drifted.filled_size <= baseline.filled_size


def test_drift_window_widens_spread() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=10.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=5000,
        liquidity_haircut_pct=0.0,
        execution_window_snapshots=3,
    )
    assert out.drifted_best_ask is not None
    assert out.drifted_best_bid is not None
    assert (out.drifted_best_ask - out.drifted_best_bid) >= (1.0 - 0.99)


def test_drift_window_never_improves_entry_price() -> None:
    now = datetime.now(tz=timezone.utc)
    baseline = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0},
            {"price": 1.01, "token_amount": 100.0, "xrp_value": 101.0},
        ],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=80.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=5000,
        liquidity_haircut_pct=0.0,
        execution_window_snapshots=0,
    )
    drifted = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0},
            {"price": 1.01, "token_amount": 100.0, "xrp_value": 101.0},
        ],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=80.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=5000,
        liquidity_haircut_pct=0.0,
        execution_window_snapshots=3,
    )
    assert baseline.avg_entry_price is not None
    assert drifted.avg_entry_price is not None
    assert drifted.avg_entry_price >= baseline.avg_entry_price


def test_drift_window_creates_no_hidden_liquidity() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 40.0, "xrp_value": 40.0},
            {"price": 1.01, "token_amount": 40.0, "xrp_value": 40.4},
            {"price": 1.02, "token_amount": 40.0, "xrp_value": 40.8},
        ],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=120.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=5000,
        liquidity_haircut_pct=0.0,
        execution_window_snapshots=3,
    )
    raw_total = sum(float(level["raw_liquidity_xrp"]) for level in out.fill_levels)
    effective_total = sum(float(level["effective_liquidity_xrp"]) for level in out.fill_levels)
    assert effective_total <= raw_total


def test_depth_walk_vwap_correctness() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0},
            {"price": 2.0, "token_amount": 100.0, "xrp_value": 200.0},
        ],
        best_bid=0.9,
        best_ask=1.0,
        requested_size_xrp=150.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.avg_entry_price == pytest.approx(1.2)


def test_one_sided_book_rejection() -> None:
    ok, reason = validate_orderbook(
        {
            "bids": [],
            "asks": [{"price": 1.0, "token_amount": 10.0, "xrp_value": 10.0}],
        }
    )
    assert ok is False
    assert reason == "INVALID_ORDERBOOK"


def test_invalid_spread_rejection() -> None:
    ok, reason = validate_orderbook(
        {
            "bids": [{"price": 1.01, "token_amount": 10.0, "xrp_value": 10.1}],
            "asks": [{"price": 1.0, "token_amount": 10.0, "xrp_value": 10.0}],
        }
    )
    assert ok is False
    assert reason == "INVALID_ORDERBOOK"


def test_exit_failure_scenario() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_exit_sell(
        bids=[],
        best_bid=0.0,
        best_ask=1.0,
        requested_token_size=10.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.fill_status == "UNFILLED"
    assert out.failure_reason == "NO_BIDS"


def test_pipeline_skips_stale_execution() -> None:
    reset_tables()
    settings = Settings(
        MIN_LIQUIDITY_XRP=1.0,
        MAX_SPREAD_PCT=50.0,
        ALPHA_STABILITY_WINDOW=3,
        ALPHA_MIN_FILL_PROBABILITY=0.0,
        ALPHA_MIN_SCORE=0.0,
        MAX_SNAPSHOT_AGE_MS=1,
        EXECUTION_LATENCY_MS=500,
    )
    pipeline = build_pipeline(settings)

    with Session(engine) as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)

        now = datetime.now(tz=timezone.utc)
        for i in range(3):
            session.add(
                MarketSnapshot(
                    token_id=token.id,
                    price_xrp=1.0,
                    liquidity_xrp=3000.0,
                    liquidity_bid_xrp=1500.0,
                    liquidity_ask_xrp=1500.0,
                    spread_pct=1.0,
                    best_bid=0.99,
                    best_ask=1.01,
                    bid_count=3,
                    ask_count=3,
                    created_at=now - timedelta(seconds=5 - i),
                )
            )
        session.commit()

        result = pipeline.run_once(session)
        outcomes = session.exec(select(PaperTradeOutcome).order_by(PaperTradeOutcome.id.desc())).all()

    assert result["signals"] >= 1
    assert any(o.failure_reason == "STALE_MARKET_DATA" for o in outcomes)


def test_queue_haircut_reduces_fill_size() -> None:
    now = datetime.now(tz=timezone.utc)
    no_haircut = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=100.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
        min_level_xrp=0.0,
        max_levels=8,
    )
    with_haircut = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=100.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.5,
        min_level_xrp=0.0,
        max_levels=8,
    )
    assert with_haircut.filled_size < no_haircut.filled_size


def test_high_queue_haircut_causes_partial_fill() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=90.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.8,
        min_level_xrp=0.0,
        max_levels=8,
    )
    assert out.fill_status == "PARTIAL"
    assert out.queue_haircut_pct == pytest.approx(0.8)


def test_latency_and_contention_reduce_effective_fill() -> None:
    now = datetime.now(tz=timezone.utc)
    baseline = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=95.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.05,
        latency_haircut_pct=0.0,
        contention_haircut_pct=0.0,
    )
    stressed = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=95.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.05,
        latency_haircut_pct=0.20,
        contention_haircut_pct=0.20,
    )
    assert stressed.filled_size < baseline.filled_size
    assert stressed.effective_liquidity_ratio < baseline.effective_liquidity_ratio


def test_trustline_discount_can_force_insufficient_depth() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=90.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
        trustline_liquidity_discount_pct=0.30,
    )
    assert out.fill_status == "PARTIAL"
    assert out.failure_reason == "INSUFFICIENT_DEPTH"


def test_ledger_drift_book_collapse_reason() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=20.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
        latency_haircut_pct=0.90,
        contention_haircut_pct=0.90,
        ledger_drift_pct=0.90,
        trustline_liquidity_discount_pct=0.40,
        min_level_xrp=1.0,
    )
    assert out.fill_status == "UNFILLED"
    assert out.failure_reason == "BOOK_COLLAPSED"


def test_deep_book_cap_enforced() -> None:
    now = datetime.now(tz=timezone.utc)
    asks = [
        {"price": 1.0 + (i * 0.01), "token_amount": 100.0, "xrp_value": 100.0 + i}
        for i in range(6)
    ]
    out = simulate_entry_buy(
        asks=asks,
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=500.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.1,
        min_level_xrp=0.0,
        max_levels=2,
    )
    assert len(out.consumed_levels_detailed) <= 2


def test_dust_levels_ignored() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 0.05, "xrp_value": 0.05},
            {"price": 1.01, "token_amount": 100.0, "xrp_value": 101.0},
        ],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=50.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
        min_level_xrp=1.0,
        max_levels=8,
    )
    assert len(out.consumed_levels_detailed) >= 1
    assert all(float(level["effective_liquidity_xrp"]) >= 1.0 for level in out.consumed_levels_detailed)


def test_fundedness_heuristic_reduces_fake_deep_wall() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 1000.0, "xrp_value": 1000.0},
            {"price": 1.01, "token_amount": 20.0, "xrp_value": 20.2},
            {"price": 1.02, "token_amount": 20.0, "xrp_value": 20.4},
        ],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=900.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
        min_level_xrp=0.0,
        max_levels=8,
    )
    assert out.fill_status in {"PARTIAL", "UNFILLED"}
    assert out.filled_size < 900.0


def test_no_asks_entry_fails_strictly() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=10.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.fill_status == "UNFILLED"
    assert out.failure_reason == "INVALID_ORDERBOOK"


def test_no_hidden_liquidity_price_improvement_assumption() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[
            {"price": 1.1, "token_amount": 100.0, "xrp_value": 110.0},
            {"price": 1.2, "token_amount": 100.0, "xrp_value": 120.0},
        ],
        best_bid=1.0,
        best_ask=1.1,
        requested_size_xrp=150.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.avg_entry_price is not None
    assert out.avg_entry_price >= 1.1


def test_canonical_mismatch_detects_canonical_gt_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_tables()
    settings = Settings(ALPHA_MIN_SCORE=0.0)
    pipeline = build_pipeline(settings)
    captured: list[dict[str, object]] = []

    def _capture(_logger, payload):
        if payload.get("event_type") == "canonical_ledger_mismatch":
            captured.append(payload)

    monkeypatch.setattr("app.execution.pipeline.log_event", _capture)

    with Session(engine) as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)

        session.add(
            Position(
                issuer=token.issuer,
                currency=token.currency,
                token_id=token.id,
                signal_id=1,
                entry_vwap=1.0,
                entry_filled_size=50.0,
                remaining_size=50.0,
                entry_orderbook_snapshot_id=1,
                status="OPEN",
            )
        )
        session.commit()

        pipeline._check_canonical_ledger_mismatch(session, token.id)

    assert len(captured) == 1
    assert captured[0]["mismatch_type"] == "canonical_gt_legacy"


def test_canonical_mismatch_detects_legacy_gt_canonical(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_tables()
    settings = Settings(ALPHA_MIN_SCORE=0.0)
    pipeline = build_pipeline(settings)
    captured: list[dict[str, object]] = []

    def _capture(_logger, payload):
        if payload.get("event_type") == "canonical_ledger_mismatch":
            captured.append(payload)

    monkeypatch.setattr("app.execution.pipeline.log_event", _capture)

    with Session(engine) as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)

        session.add(
            PaperTradeOutcome(
                token_id=token.id,
                signal_id=1,
                snapshot_id=None,
                entry_price=1.0,
                expected_slippage_pct=0.0,
                actual_slippage_pct=0.0,
                target_size_xrp=50.0,
                filled_size_xrp=50.0,
                fill_success=True,
                partial_fill=False,
                fill_status="FILLED",
            )
        )
        session.commit()

        pipeline._check_canonical_ledger_mismatch(session, token.id)

    assert len(captured) == 1
    assert captured[0]["mismatch_type"] == "legacy_gt_canonical"


def test_canonical_mismatch_detects_semantic_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_tables()
    settings = Settings(ALPHA_MIN_SCORE=0.0)
    pipeline = build_pipeline(settings)
    captured: list[dict[str, object]] = []

    def _capture(_logger, payload):
        if payload.get("event_type") == "canonical_ledger_mismatch":
            captured.append(payload)

    monkeypatch.setattr("app.execution.pipeline.log_event", _capture)

    with Session(engine) as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)

        session.add(
            Position(
                issuer=token.issuer,
                currency=token.currency,
                token_id=token.id,
                signal_id=1,
                entry_vwap=1.0,
                entry_filled_size=70.0,
                exit_filled_size=0.0,
                remaining_size=70.0,
                entry_orderbook_snapshot_id=1,
                status="OPEN",
            )
        )
        session.add(
            PaperTradeOutcome(
                token_id=token.id,
                signal_id=1,
                snapshot_id=None,
                entry_price=1.0,
                expected_slippage_pct=0.0,
                actual_slippage_pct=0.0,
                target_size_xrp=70.0,
                filled_size_xrp=70.0,
                fill_success=True,
                partial_fill=False,
                fill_status="FILLED",
                exit_time=datetime.now(tz=timezone.utc),
                exit_price=1.1,
            )
        )
        session.commit()

        pipeline._check_canonical_ledger_mismatch(session, token.id)

    assert len(captured) == 1
    assert captured[0]["mismatch_type"] == "semantic_mismatch"


def test_failed_inclusion_creates_no_position(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_tables()
    settings = Settings(
        MIN_LIQUIDITY_XRP=1.0,
        MAX_SPREAD_PCT=50.0,
        ALPHA_STABILITY_WINDOW=3,
        ALPHA_MIN_FILL_PROBABILITY=0.0,
        ALPHA_MIN_SCORE=0.0,
    )
    pipeline = build_pipeline(settings)
    monkeypatch.setattr(
        pipeline.alpha_engine,
        "evaluate",
        lambda **kwargs: SimpleNamespace(
            pair="USD:rIssuer",
            score=0.99,
            decision="APPROVE",
            reasons=[],
            spread=1.0,
            depth_xrp=10000.0,
            imbalance=0.0,
            slippage_estimate=0.0,
            fill_probability=1.0,
            stability_score=1.0,
            spread_stability=1.0,
            liquidity_consistency=1.0,
            mid_price_stability=1.0,
            component_scores={},
            manipulation_flags={},
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "_simulate_inclusion_uncertainty",
        lambda signal_id, snapshot_id: {"status": "FAILED_INCLUSION", "delay_ledgers": 1, "failure_reason": "SIM_FAIL"},
    )

    with Session(engine) as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()

        pipeline.run_once(session)
        positions = session.exec(select(Position)).all()
        executions = session.exec(select(ExecutionRecord)).all()

    assert len(positions) == 0
    assert any(e.inclusion_status == "FAILED_INCLUSION" for e in executions)


def test_delayed_inclusion_worsens_fill() -> None:
    settings = Settings(ALPHA_MIN_SCORE=0.0)
    pipeline = build_pipeline(settings)
    now = datetime.now(tz=timezone.utc)
    fill = simulate_entry_buy(
        asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        best_bid=0.99,
        best_ask=1.0,
        requested_size_xrp=80.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    baseline = fill.filled_size
    degraded = pipeline._apply_inclusion_uncertainty(
        fill,
        {"status": "DELAYED", "delay_ledgers": 2, "failure_reason": None},
    )
    assert degraded.filled_size < baseline


def test_inclusion_failure_releases_reserved_capital(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_tables()
    settings = Settings(
        MIN_LIQUIDITY_XRP=1.0,
        MAX_SPREAD_PCT=50.0,
        ALPHA_STABILITY_WINDOW=3,
        ALPHA_MIN_FILL_PROBABILITY=0.0,
        ALPHA_MIN_SCORE=0.0,
    )
    pipeline = build_pipeline(settings)
    monkeypatch.setattr(
        pipeline.alpha_engine,
        "evaluate",
        lambda **kwargs: SimpleNamespace(
            pair="USD:rIssuer",
            score=0.99,
            decision="APPROVE",
            reasons=[],
            spread=1.0,
            depth_xrp=10000.0,
            imbalance=0.0,
            slippage_estimate=0.0,
            fill_probability=1.0,
            stability_score=1.0,
            spread_stability=1.0,
            liquidity_consistency=1.0,
            mid_price_stability=1.0,
            component_scores={},
            manipulation_flags={},
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "_simulate_inclusion_uncertainty",
        lambda signal_id, snapshot_id: {"status": "FAILED_INCLUSION", "delay_ledgers": 1, "failure_reason": "SIM_FAIL"},
    )

    with Session(engine) as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()

        pipeline.run_once(session)
        reservation = session.exec(select(CapitalReservation).order_by(CapitalReservation.id.desc())).first()

    assert reservation is not None
    assert reservation.status == "RELEASED"
    assert reservation.deployed_xrp == pytest.approx(0.0)


def test_inclusion_status_persisted(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_tables()
    settings = Settings(
        MIN_LIQUIDITY_XRP=1.0,
        MAX_SPREAD_PCT=50.0,
        ALPHA_STABILITY_WINDOW=3,
        ALPHA_MIN_FILL_PROBABILITY=0.0,
        ALPHA_MIN_SCORE=0.0,
    )
    pipeline = build_pipeline(settings)
    monkeypatch.setattr(
        pipeline.alpha_engine,
        "evaluate",
        lambda **kwargs: SimpleNamespace(
            pair="USD:rIssuer",
            score=0.99,
            decision="APPROVE",
            reasons=[],
            spread=1.0,
            depth_xrp=10000.0,
            imbalance=0.0,
            slippage_estimate=0.0,
            fill_probability=1.0,
            stability_score=1.0,
            spread_stability=1.0,
            liquidity_consistency=1.0,
            mid_price_stability=1.0,
            component_scores={},
            manipulation_flags={},
        ),
    )
    monkeypatch.setattr(
        pipeline,
        "_simulate_inclusion_uncertainty",
        lambda signal_id, snapshot_id: {"status": "DELAYED", "delay_ledgers": 2, "failure_reason": None},
    )

    with Session(engine) as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()

        pipeline.run_once(session)
        record = session.exec(select(ExecutionRecord).order_by(ExecutionRecord.id.desc())).first()

    assert record is not None
    assert record.inclusion_status == "DELAYED"
    assert record.inclusion_delay_ledgers == 2


def test_no_residual_midpoint_slippage_naming_in_execution_paths() -> None:
    roots = [
        Path("app/execution/pnl_attribution_engine.py"),
        Path("app/execution/pipeline.py"),
        Path("tests/test_pnl_attribution_strict.py"),
    ]
    for path in roots:
        text = path.read_text(encoding="utf-8")
        assert "entry_slippage_vs_mid" not in text
        assert "slippage_vs_mid" not in text
