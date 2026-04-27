from datetime import datetime, timedelta, timezone

import pytest

from sqlmodel import Session, select

from app.alpha.engine import AlphaEngine
from app.alpha.performance_engine import PerformanceEngine
from app.config import Settings
from app.db.models import (
    AlphaCooldownRecord,
    AlphaSignal,
    ExecutionRecord,
    MarketDepthLevel,
    MarketSnapshot,
    PaperTradeOutcome,
    Position,
    PositionExitFill,
    RiskDecisionRecord,
    RiskEvent,
    Signal,
    WatchedToken,
)
from app.db.session import engine, init_db
from app.execution.fill_simulator import simulate_fill
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
                    {"quality": 0.98, "taker_gets": 980.0, "taker_pays": 1000.0},
                    {"quality": 0.97, "taker_gets": 1164.0, "taker_pays": 1200.0},
                    {"quality": 0.96, "taker_gets": 672.0, "taker_pays": 700.0},
                ]
            }
        return {
            "offers": [
                {"quality": 1.01, "taker_gets": 900.0, "taker_pays": 909.0},
                {"quality": 1.02, "taker_gets": 1100.0, "taker_pays": 1122.0},
                {"quality": 1.03, "taker_gets": 800.0, "taker_pays": 824.0},
            ]
        }


def reset_tables() -> None:
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
    strategy_registry = StrategyRegistry()
    strategy_registry.register(NewTokenScannerStrategy(settings=settings))
    risk_manager = RiskManager(settings, KillSwitch())
    paper_executor = PaperExecutor(settings)
    alpha_engine = AlphaEngine(settings)
    return ExecutionPipeline(settings, FakeXRPLClient(), strategy_registry, risk_manager, paper_executor, alpha_engine)


def test_partial_fill_simulation() -> None:
    asks = [
        {"price": 1.0, "token_amount": 1.0, "xrp_value": 1.0},
        {"price": 1.1, "token_amount": 1.0, "xrp_value": 1.1},
    ]
    out = simulate_fill(asks, target_size_xrp=3.0)

    assert out["partial_fill"] is True
    assert out["fill_success"] is False
    assert out["filled_size_xrp"] == 2.1


def test_zero_liquidity_fill_simulation() -> None:
    out = simulate_fill([], target_size_xrp=1.0)

    assert out["fill_success"] is False
    assert out["filled_size_xrp"] == 0.0
    assert out["slippage_pct"] == 100.0


def test_slippage_mismatch_metric() -> None:
    reset_tables()
    with Session(engine) as session:
        token = WatchedToken(issuer="rA", currency="USD")
        signal = Signal(
            strategy_name="test",
            issuer="rA",
            currency="USD",
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=2.0,
            reason="unit",
        )
        session.add(token)
        session.add(signal)
        session.commit()
        session.refresh(token)
        session.refresh(signal)

        row = PaperTradeOutcome(
            token_id=token.id,
            signal_id=signal.id,
            snapshot_id=None,
            entry_price=1.0,
            expected_slippage_pct=0.2,
            actual_slippage_pct=0.7,
            target_size_xrp=2.0,
            filled_size_xrp=2.0,
            fill_success=True,
            partial_fill=False,
            entry_time=datetime.now(tz=timezone.utc),
            exit_time=datetime.now(tz=timezone.utc),
            exit_price=1.05,
            pnl_xrp=0.1,
            reason_closed="test",
        )
        session.add(row)
        session.commit()

        perf = PerformanceEngine(Settings())
        summary = perf.summary(session)

    assert summary["trades"] == 1
    assert summary["avg_slippage_error"] == pytest.approx(0.5)


def test_mae_mfe_tracking_correctness() -> None:
    reset_tables()
    settings = Settings(PERF_MONITOR_MINUTES=30)
    pipeline = build_pipeline(settings)

    with Session(engine) as session:
        token = WatchedToken(issuer="rB", currency="EUR")
        signal = Signal(
            strategy_name="test",
            issuer="rB",
            currency="EUR",
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=3.0,
            reason="unit",
        )
        session.add(token)
        session.add(signal)
        session.commit()
        session.refresh(token)
        session.refresh(signal)

        outcome = PaperTradeOutcome(
            token_id=token.id,
            signal_id=signal.id,
            snapshot_id=None,
            entry_price=1.0,
            expected_slippage_pct=0.0,
            actual_slippage_pct=0.0,
            target_size_xrp=3.0,
            filled_size_xrp=3.0,
            fill_success=True,
            partial_fill=False,
            entry_time=datetime.now(tz=timezone.utc),
        )
        session.add(outcome)
        session.commit()
        session.refresh(outcome)

        down_snapshot = MarketSnapshot(token_id=token.id, price_xrp=0.9, liquidity_xrp=3000.0, bid_count=3, ask_count=3)
        session.add(down_snapshot)
        session.commit()
        session.refresh(down_snapshot)
        pipeline._update_open_outcomes_for_token(session, token.id, down_snapshot)

        up_snapshot = MarketSnapshot(token_id=token.id, price_xrp=1.2, liquidity_xrp=3000.0, bid_count=3, ask_count=3)
        session.add(up_snapshot)
        session.commit()
        session.refresh(up_snapshot)
        pipeline._update_open_outcomes_for_token(session, token.id, up_snapshot)

        refreshed = session.get(PaperTradeOutcome, outcome.id)

    assert refreshed is not None
    assert refreshed.max_adverse_excursion_pct >= 9.99
    assert refreshed.max_favorable_excursion_pct >= 19.99


def test_signal_to_outcome_linking() -> None:
    reset_tables()
    with Session(engine) as session:
        token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
        session.add(token)
        session.commit()
        session.refresh(token)

        signal = Signal(
            strategy_name="unit",
            issuer=token.issuer,
            currency=token.currency,
            side="BUY",
            confidence=0.9,
            risk_score=0.1,
            suggested_size_xrp=2.0,
            reason="unit",
        )
        session.add(signal)
        session.commit()
        session.refresh(signal)

        outcome = PaperTradeOutcome(
            token_id=token.id,
            signal_id=signal.id,
            snapshot_id=None,
            entry_price=1.0,
            expected_slippage_pct=0.1,
            actual_slippage_pct=0.2,
            target_size_xrp=2.0,
            filled_size_xrp=2.0,
            fill_success=True,
            partial_fill=False,
            entry_time=datetime.now(tz=timezone.utc),
        )
        session.add(outcome)
        session.commit()

        outcome = session.exec(select(PaperTradeOutcome).order_by(PaperTradeOutcome.id.desc())).first()
        signal = session.exec(select(Signal).order_by(Signal.id.desc())).first()

    assert outcome is not None
    assert signal is not None
    assert outcome.signal_id == signal.id


def test_performance_aggregation() -> None:
    reset_tables()
    with Session(engine) as session:
        token = WatchedToken(issuer="rC", currency="JPY")
        session.add(token)
        session.commit()
        session.refresh(token)

        signal_a = Signal(
            strategy_name="s1",
            issuer="rC",
            currency="JPY",
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=2.0,
            reason="unit",
        )
        signal_b = Signal(
            strategy_name="s1",
            issuer="rC",
            currency="JPY",
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=2.0,
            reason="unit",
        )
        session.add(signal_a)
        session.add(signal_b)
        session.commit()
        session.refresh(signal_a)
        session.refresh(signal_b)

        session.add(
            AlphaSignal(
                token_id=token.id,
                snapshot_id=None,
                pair="JPY:rC",
                score=0.8,
                decision="APPROVE",
                reasons_json="[]",
                component_scores_json='{"spread_quality_score": 0.9}',
                manipulation_flags_json='{"liquidity_concentrated": true}',
            )
        )

        session.add(
            PaperTradeOutcome(
                token_id=token.id,
                signal_id=signal_a.id,
                snapshot_id=None,
                entry_price=1.0,
                expected_slippage_pct=0.1,
                actual_slippage_pct=0.2,
                target_size_xrp=2.0,
                filled_size_xrp=2.0,
                fill_success=True,
                partial_fill=False,
                entry_time=datetime.now(tz=timezone.utc),
                exit_time=datetime.now(tz=timezone.utc),
                exit_price=1.1,
                pnl_xrp=0.2,
                reason_closed="done",
            )
        )
        session.add(
            PaperTradeOutcome(
                token_id=token.id,
                signal_id=signal_b.id,
                snapshot_id=None,
                entry_price=1.0,
                expected_slippage_pct=0.2,
                actual_slippage_pct=0.4,
                target_size_xrp=2.0,
                filled_size_xrp=1.0,
                fill_success=False,
                partial_fill=True,
                entry_time=datetime.now(tz=timezone.utc),
                exit_time=datetime.now(tz=timezone.utc),
                exit_price=0.95,
                pnl_xrp=-0.05,
                reason_closed="fill_failed",
            )
        )
        session.commit()

        perf = PerformanceEngine(Settings())
        summary = perf.summary(session)
        breakdown = perf.alpha_breakdown(session)

    assert summary["trades"] == 2
    assert summary["fill_rate"] == 0.5
    assert summary["avg_pnl"] < 0.2
    assert "components" in breakdown
    assert "manipulation_flags" in breakdown
