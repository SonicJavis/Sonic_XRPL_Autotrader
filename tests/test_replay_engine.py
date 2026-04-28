from datetime import datetime, timezone

from sqlmodel import Session, select

from app.db.models import (
    AlphaCooldownRecord,
    AlphaSignal,
    CapitalLedger,
    CapitalReservation,
    ExecutionFillSlice,
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
from app.execution.fill_simulator import simulate_entry_buy, simulate_exit_sell
from app.execution.pnl_attribution_engine import PnLAttributionEngine
from app.execution.replay_engine import ReplayEngine


def reset_tables() -> None:
    CapitalReservation.__table__.drop(engine, checkfirst=True)
    CapitalLedger.__table__.drop(engine, checkfirst=True)
    PaperTrade.__table__.drop(engine, checkfirst=True)
    PositionExitFill.__table__.drop(engine, checkfirst=True)
    ExecutionFillSlice.__table__.drop(engine, checkfirst=True)
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


def _mk_token_signal(session: Session) -> tuple[WatchedToken, Signal]:
    token = WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False)
    session.add(token)
    session.commit()
    session.refresh(token)

    sig = Signal(
        strategy_name="unit",
        issuer=token.issuer,
        currency=token.currency,
        side="BUY",
        confidence=0.9,
        risk_score=0.1,
        suggested_size_xrp=200.0,
        reason="unit",
    )
    session.add(sig)
    session.commit()
    session.refresh(sig)
    return token, sig


def _mk_snapshot(session: Session, token_id: int) -> MarketSnapshot:
    snap = MarketSnapshot(
        token_id=token_id,
        price_xrp=1.0,
        liquidity_xrp=5000.0,
        liquidity_bid_xrp=2500.0,
        liquidity_ask_xrp=2500.0,
        spread_pct=1.0,
        best_bid=1.0,
        best_ask=1.1,
        bid_count=2,
        ask_count=2,
    )
    session.add(snap)
    session.commit()
    session.refresh(snap)
    return snap


def test_replay_reproduces_entry_execution() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        snap = _mk_snapshot(session, token.id)
        out = simulate_entry_buy(
            asks=[{"price": 1.1, "token_amount": 200.0, "xrp_value": 220.0}],
            best_bid=1.0,
            best_ask=1.1,
            requested_size_xrp=50.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=5000,
            liquidity_haircut_pct=0.0,
        )
        rec = PnLAttributionEngine().create_execution_record(
            session,
            token_id=token.id,
            signal_id=sig.id,
            risk_decision_id=None,
            snapshot_id=snap.id,
            position_id=None,
            side="BUY",
            execution_result=out,
            snapshot_time=now,
            signal_time=now,
            execution_time=now,
            ledger_index_snapshot=10,
            ledger_index_signal=11,
            ledger_index_execution=11,
            ledger_index_inclusion=13,
            inclusion_status="DELAYED",
            min_ledger_delay=1,
            max_ledger_delay=3,
        )
        replay = ReplayEngine().replay_execution(session, rec.id)

    assert replay["status"] == "REPLAY_OK"
    assert replay["filled_size"] == rec.filled_size


def test_replay_reproduces_exit_execution() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        snap = _mk_snapshot(session, token.id)
        out = simulate_exit_sell(
            bids=[{"price": 1.2, "token_amount": 50.0, "xrp_value": 60.0}],
            best_bid=1.2,
            best_ask=1.3,
            requested_token_size=20.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=5000,
            liquidity_haircut_pct=0.0,
        )
        rec = PnLAttributionEngine().create_execution_record(
            session,
            token_id=token.id,
            signal_id=sig.id,
            risk_decision_id=None,
            snapshot_id=snap.id,
            position_id=None,
            side="SELL",
            execution_result=out,
            snapshot_time=now,
            signal_time=now,
            execution_time=now,
            ledger_index_snapshot=10,
            ledger_index_signal=11,
            ledger_index_execution=11,
            ledger_index_inclusion=12,
            inclusion_status="INCLUDED",
            min_ledger_delay=1,
            max_ledger_delay=3,
        )
        replay = ReplayEngine().replay_execution(session, rec.id)

    assert replay["status"] == "REPLAY_OK"
    assert replay["fill_status"] in {"FILLED", "PARTIAL", "UNFILLED"}


def test_replay_reproduces_realized_pnl() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        snap = _mk_snapshot(session, token.id)
        out = simulate_exit_sell(
            bids=[{"price": 1.2, "token_amount": 50.0, "xrp_value": 60.0}],
            best_bid=1.2,
            best_ask=1.3,
            requested_token_size=20.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=5000,
            liquidity_haircut_pct=0.0,
        )
        rec = PnLAttributionEngine().create_execution_record(
            session,
            token_id=token.id,
            signal_id=sig.id,
            risk_decision_id=None,
            snapshot_id=snap.id,
            position_id=None,
            side="SELL",
            execution_result=out,
            snapshot_time=now,
            signal_time=now,
            execution_time=now,
            ledger_index_snapshot=10,
            ledger_index_signal=11,
            ledger_index_execution=11,
            ledger_index_inclusion=12,
            inclusion_status="INCLUDED",
            min_ledger_delay=1,
            max_ledger_delay=3,
        )
        session.add(
            PositionExitFill(
                position_id="unit-pos",
                execution_id=rec.id,
                snapshot_id=snap.id,
                exit_vwap=float(out.avg_exit_price or 0.0),
                fill_size=float(out.filled_size),
                pnl_xrp=1.234,
            )
        )
        session.commit()

        replay = ReplayEngine().replay_execution(session, rec.id)

    assert replay["status"] == "REPLAY_OK"
    assert replay["realized_pnl_xrp"] == 1.234


def test_modified_fill_levels_cause_replay_mismatch() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        snap = _mk_snapshot(session, token.id)
        out = simulate_entry_buy(
            asks=[{"price": 1.1, "token_amount": 200.0, "xrp_value": 220.0}],
            best_bid=1.0,
            best_ask=1.1,
            requested_size_xrp=50.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=5000,
            liquidity_haircut_pct=0.0,
        )
        rec = PnLAttributionEngine().create_execution_record(
            session,
            token_id=token.id,
            signal_id=sig.id,
            risk_decision_id=None,
            snapshot_id=snap.id,
            position_id=None,
            side="BUY",
            execution_result=out,
            snapshot_time=now,
            signal_time=now,
            execution_time=now,
            ledger_index_snapshot=10,
            ledger_index_signal=11,
            ledger_index_execution=11,
            ledger_index_inclusion=12,
            inclusion_status="INCLUDED",
            min_ledger_delay=1,
            max_ledger_delay=3,
        )
        first_slice = session.exec(
            select(ExecutionFillSlice)
            .where(ExecutionFillSlice.execution_id == rec.id)
            .order_by(ExecutionFillSlice.id.asc())
        ).first()
        assert first_slice is not None
        first_slice.fill_levels_json = [{"tampered": 1}]
        session.add(first_slice)
        session.commit()

        replay = ReplayEngine().replay_execution(session, rec.id)

    assert replay["status"] == "REPLAY_MISMATCH"
    assert "slice_levels_checksum_mismatch" in replay["mismatches"]
