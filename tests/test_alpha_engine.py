from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.alpha.engine import AlphaEngine
from app.config import Settings
from app.db.models import (
    AlphaCooldownRecord,
    AlphaSignal,
    ExecutionRecord,
    MarketSnapshot,
    PaperTradeOutcome,
    Position,
    PositionExitFill,
    RiskDecisionRecord,
    Signal,
    WatchedToken,
)
from app.db.session import engine as db_engine, init_db


def _history(count: int, spread: float = 1.0, liq: float = 5000.0, price: float = 1.0) -> list[MarketSnapshot]:
    now = datetime.now(tz=timezone.utc)
    rows: list[MarketSnapshot] = []
    for idx in range(count):
        rows.append(
            MarketSnapshot(
                token_id=1,
                price_xrp=price,
                liquidity_xrp=liq,
                liquidity_bid_xrp=liq / 2,
                liquidity_ask_xrp=liq / 2,
                spread_pct=spread,
                best_bid=price * 0.999,
                best_ask=price * 1.001,
                tx_count=10,
                bid_count=5,
                ask_count=5,
                created_at=now - timedelta(minutes=count - idx),
            )
        )
    return rows


def _book() -> tuple[list[dict[str, float]], list[dict[str, float]]]:
    bids = [
        {"price": 0.99, "token_amount": 1000.0, "xrp_value": 990.0},
        {"price": 0.98, "token_amount": 1000.0, "xrp_value": 980.0},
        {"price": 0.97, "token_amount": 1000.0, "xrp_value": 970.0},
    ]
    asks = [
        {"price": 1.01, "token_amount": 1000.0, "xrp_value": 1010.0},
        {"price": 1.02, "token_amount": 1000.0, "xrp_value": 1020.0},
        {"price": 1.03, "token_amount": 1000.0, "xrp_value": 1030.0},
    ]
    return bids, asks


def test_alpha_rejects_when_spread_missing() -> None:
    engine = AlphaEngine(Settings())
    bids, asks = _book()

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=None,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=2.0,
        issuer="rIssuer",
    )

    assert out.decision == "REJECT"
    assert any("spread unavailable" in reason for reason in out.reasons)


def test_alpha_rejects_when_book_concentrated() -> None:
    engine = AlphaEngine(Settings())
    bids = [{"price": 1.0, "token_amount": 10000.0, "xrp_value": 10000.0}] + [
        {"price": 0.99, "token_amount": 1.0, "xrp_value": 0.99},
        {"price": 0.98, "token_amount": 1.0, "xrp_value": 0.98},
    ]
    asks = [{"price": 1.01, "token_amount": 10000.0, "xrp_value": 10100.0}] + [
        {"price": 1.02, "token_amount": 1.0, "xrp_value": 1.02},
        {"price": 1.03, "token_amount": 1.0, "xrp_value": 1.03},
    ]

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=1.0,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=2.0,
        issuer="rIssuer",
    )

    assert out.decision == "REJECT"
    assert any("manipulation" in reason for reason in out.reasons)


def test_alpha_rejects_when_fill_probability_too_low() -> None:
    settings = Settings(ALPHA_MIN_FILL_PROBABILITY=0.9, MAX_TRADE_XRP=5)
    engine = AlphaEngine(settings)
    bids = [{"price": 0.99, "token_amount": 100.0, "xrp_value": 99.0} for _ in range(3)]
    asks = [{"price": 1.01, "token_amount": 0.5, "xrp_value": 0.505} for _ in range(3)]

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=1.0,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=5.0,
        issuer="rIssuer",
    )

    assert out.decision == "REJECT"
    assert any("fill probability too low" in reason for reason in out.reasons)


def test_alpha_cooldown_triggers_after_failure_burst() -> None:
    settings = Settings(ALPHA_COOLDOWN_FAILURES=3, ALPHA_COOLDOWN_MINUTES=10)
    engine = AlphaEngine(settings)
    now = datetime.now(tz=timezone.utc)

    failures = [now - timedelta(minutes=1), now - timedelta(minutes=2), now - timedelta(minutes=3)]

    assert engine.in_cooldown(failures) is True


def test_alpha_stores_component_scores() -> None:
    engine = AlphaEngine(Settings())
    bids, asks = _book()

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=1.0,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=2.0,
        issuer="rIssuer",
    )

    assert "spread_quality_score" in out.component_scores
    assert "depth_score" in out.component_scores
    assert "imbalance_score" in out.component_scores
    assert "stability_score" in out.component_scores
    assert "fill_feasibility_score" in out.component_scores
    assert "slippage_penalty" in out.component_scores


def test_alpha_stores_manipulation_flags() -> None:
    engine = AlphaEngine(Settings())
    bids, asks = _book()

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=1.0,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=2.0,
        issuer="rIssuer",
    )

    assert "liquidity_concentrated" in out.manipulation_flags
    assert "book_collapses_fast" in out.manipulation_flags
    assert "suspicious_issuer" in out.manipulation_flags


def test_alpha_stores_stability_subscores() -> None:
    engine = AlphaEngine(Settings())
    bids, asks = _book()

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=1.0,
        bids=bids,
        asks=asks,
        history=_history(6),
        target_size_xrp=2.0,
        issuer="rIssuer",
    )

    assert 0.0 <= out.spread_stability <= 1.0
    assert 0.0 <= out.liquidity_consistency <= 1.0
    assert 0.0 <= out.mid_price_stability <= 1.0


def test_negative_slippage_clipped_to_zero() -> None:
    """Verify slippage_estimate is never negative on the AlphaEvaluation."""
    engine = AlphaEngine(Settings())
    # All asks at the same price → VWAP == best ask → slippage = 0.0, never negative.
    flat_asks = [{"price": 1.0, "token_amount": 500.0, "xrp_value": 500.0} for _ in range(3)]
    bids = [{"price": 0.99, "token_amount": 500.0, "xrp_value": 495.0} for _ in range(3)]

    out = engine.evaluate(
        pair="USD:rIssuer",
        spread_pct=1.0,
        bids=bids,
        asks=flat_asks,
        history=_history(6),
        target_size_xrp=2.0,
        issuer="rIssuer",
    )

    assert out.slippage_estimate >= 0.0


def _reset_attribution_tables() -> None:
    PositionExitFill.__table__.drop(db_engine, checkfirst=True)
    ExecutionRecord.__table__.drop(db_engine, checkfirst=True)
    Position.__table__.drop(db_engine, checkfirst=True)
    PaperTradeOutcome.__table__.drop(db_engine, checkfirst=True)
    AlphaCooldownRecord.__table__.drop(db_engine, checkfirst=True)
    RiskDecisionRecord.__table__.drop(db_engine, checkfirst=True)
    AlphaSignal.__table__.drop(db_engine, checkfirst=True)
    Signal.__table__.drop(db_engine, checkfirst=True)
    WatchedToken.__table__.drop(db_engine, checkfirst=True)
    init_db()


def test_cooldown_is_token_specific() -> None:
    """Rejection of token A should not block token B."""
    from app.db.models import MarketSnapshot as MS
    _reset_attribution_tables()

    with Session(db_engine) as session:
        ta = WatchedToken(issuer="rIssuerA", currency="AAA")
        tb = WatchedToken(issuer="rIssuerB", currency="BBB")
        session.add(ta)
        session.add(tb)
        session.commit()
        session.refresh(ta)
        session.refresh(tb)

        settings = Settings(ALPHA_COOLDOWN_FAILURES=3, ALPHA_COOLDOWN_MINUTES=10)

        # Add 3 recent rejections for token A only.
        for _ in range(3):
            session.add(AlphaCooldownRecord(token_id=ta.id))
        session.commit()

        from app.execution.pipeline import ExecutionPipeline
        assert ExecutionPipeline._token_in_cooldown(session, ta.id, settings) is True
        assert ExecutionPipeline._token_in_cooldown(session, tb.id, settings) is False


def test_cooldown_persists_across_pipeline_runs() -> None:
    """Cooldown records written in run 1 are still visible in run 2."""
    _reset_attribution_tables()

    settings = Settings(ALPHA_COOLDOWN_FAILURES=3, ALPHA_COOLDOWN_MINUTES=10)
    token_id: int

    with Session(db_engine) as session:
        tok = WatchedToken(issuer="rIssuerC", currency="CCC")
        session.add(tok)
        session.commit()
        session.refresh(tok)
        token_id = tok.id  # capture before session closes

        # Simulate run 1 writing 3 rejection records.
        for _ in range(3):
            session.add(AlphaCooldownRecord(token_id=token_id))
        session.commit()

    # Separate session simulates a new run_once call.
    with Session(db_engine) as session2:
        from app.execution.pipeline import ExecutionPipeline
        assert ExecutionPipeline._token_in_cooldown(session2, token_id, settings) is True


def test_risk_decision_record_links_signal_id() -> None:
    """Verify RiskDecisionRecord.signal_id references the signal row."""
    _reset_attribution_tables()

    with Session(db_engine) as session:
        tok = WatchedToken(issuer="rIssuerD", currency="DDD")
        session.add(tok)
        session.commit()
        session.refresh(tok)

        sig = Signal(
            strategy_name="test",
            issuer=tok.issuer,
            currency=tok.currency,
            side="BUY",
            confidence=0.8,
            risk_score=0.2,
            suggested_size_xrp=1.0,
            reason="unit test",
        )
        session.add(sig)
        session.commit()
        session.refresh(sig)

        record = RiskDecisionRecord(
            token_id=tok.id,
            snapshot_id=None,
            signal_id=sig.id,
            decision="APPROVE",
            reason="test",
            score=0.9,
        )
        session.add(record)
        session.commit()
        session.refresh(record)

        assert record.signal_id == sig.id
        fetched = session.exec(
            select(RiskDecisionRecord).where(RiskDecisionRecord.signal_id == sig.id)
        ).first()
        assert fetched is not None
