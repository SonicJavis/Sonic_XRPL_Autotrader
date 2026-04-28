from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlmodel import Session, select

from app.alpha.engine import AlphaEngine
from app.config import Settings
from app.db.models import (
    AlphaCooldownRecord,
    AlphaSignal,
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
                fill_status="FULL",
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
                fill_status="FULL",
                exit_time=datetime.now(tz=timezone.utc),
                exit_price=1.1,
            )
        )
        session.commit()

        pipeline._check_canonical_ledger_mismatch(session, token.id)

    assert len(captured) == 1
    assert captured[0]["mismatch_type"] == "semantic_mismatch"


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
