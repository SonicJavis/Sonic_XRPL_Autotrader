from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

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
from app.execution.fill_simulator import simulate_entry_buy
from app.execution.pnl_attribution_engine import PnLAttributionEngine


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


def _mk_snapshot_with_depth(session: Session, token_id: int, bids: list[dict[str, float]], asks: list[dict[str, float]]) -> MarketSnapshot:
    snap = MarketSnapshot(
        token_id=token_id,
        price_xrp=1.0,
        liquidity_xrp=10000.0,
        liquidity_bid_xrp=sum(x["xrp_value"] for x in bids),
        liquidity_ask_xrp=sum(x["xrp_value"] for x in asks),
        spread_pct=1.0,
        best_bid=(bids[0]["price"] if bids else None),
        best_ask=(asks[0]["price"] if asks else None),
        bid_count=len(bids),
        ask_count=len(asks),
    )
    session.add(snap)
    session.commit()
    session.refresh(snap)

    for i, row in enumerate(bids):
        session.add(
            MarketDepthLevel(
                snapshot_id=snap.id,
                side="bid",
                level_index=i,
                price_xrp_per_token=row["price"],
                token_amount=row["token_amount"],
                xrp_value=row["xrp_value"],
                cumulative_xrp=sum(x["xrp_value"] for x in bids[: i + 1]),
            )
        )
    for i, row in enumerate(asks):
        session.add(
            MarketDepthLevel(
                snapshot_id=snap.id,
                side="ask",
                level_index=i,
                price_xrp_per_token=row["price"],
                token_amount=row["token_amount"],
                xrp_value=row["xrp_value"],
                cumulative_xrp=sum(x["xrp_value"] for x in asks[: i + 1]),
            )
        )
    session.commit()
    return snap


def test_partial_entry_correct_position_size() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    entry_filled: float
    remaining: float
    fill_status: str
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 0.99, "token_amount": 1000.0, "xrp_value": 990.0}],
            asks=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
        )
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
        engine_attrib = PnLAttributionEngine()
        exec_row = engine_attrib.create_execution_record(
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
        )
        pos = engine_attrib.create_position_from_entry(
            session,
            token_id=token.id,
            issuer=token.issuer,
            currency=token.currency,
            signal_id=sig.id,
            risk_decision_id=None,
            execution_record_id=exec_row.id,
            snapshot_id=snap.id,
            execution_result=out,
            alpha_signal=None,
            execution_time=now,
        )
        assert pos is not None
        entry_filled = pos.entry_filled_size
        remaining = pos.remaining_size
        fill_status = out.fill_status

    assert fill_status == "PARTIAL"
    assert entry_filled == pytest.approx(out.filled_size)
    assert remaining == pytest.approx(out.filled_size)


def test_partial_exit_correct_realized_pnl() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        entry_snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 0.99, "token_amount": 1000.0, "xrp_value": 990.0}],
            asks=[{"price": 1.0, "token_amount": 1000.0, "xrp_value": 1000.0}],
        )
        out = simulate_entry_buy(
            asks=[{"price": 1.0, "token_amount": 1000.0, "xrp_value": 1000.0}],
            best_bid=0.99,
            best_ask=1.0,
            requested_size_xrp=200.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
        )
        eng = PnLAttributionEngine()
        exec_row = eng.create_execution_record(
            session,
            token_id=token.id,
            signal_id=sig.id,
            risk_decision_id=None,
            snapshot_id=entry_snap.id,
            position_id=None,
            side="BUY",
            execution_result=out,
            snapshot_time=now,
            signal_time=now,
            execution_time=now,
        )
        pos = eng.create_position_from_entry(
            session,
            token_id=token.id,
            issuer=token.issuer,
            currency=token.currency,
            signal_id=sig.id,
            risk_decision_id=None,
            execution_record_id=exec_row.id,
            snapshot_id=entry_snap.id,
            execution_result=out,
            alpha_signal=None,
            execution_time=now,
        )
        assert pos is not None
        pos.status = "PARTIAL_EXIT"
        session.add(pos)
        session.commit()

        # Only half of tokens can exit.
        requested_tokens = pos.remaining_size / pos.entry_vwap
        _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.2, "token_amount": requested_tokens / 2.0, "xrp_value": (requested_tokens / 2.0) * 1.2}],
            asks=[{"price": 1.3, "token_amount": 1000.0, "xrp_value": 1300.0}],
        )
        latest = session.exec(select(MarketSnapshot).where(MarketSnapshot.token_id == token.id).order_by(MarketSnapshot.id.desc())).first()
        eng.update_positions_for_snapshot(
            session,
            token_id=token.id,
            snapshot=latest,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
            min_exit_retry_ms=0,
            max_exit_retries=5,
            approve_exit_fn=lambda p, s: True,
        )
        fills = session.exec(select(PositionExitFill).where(PositionExitFill.position_id == pos.position_id)).all()

    assert len(fills) == 1
    expected = (1.2 - pos.entry_vwap) * fills[0].fill_size
    assert fills[0].pnl_xrp == pytest.approx(expected)


def test_no_bids_exit_failure() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        entry_snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 0.99, "token_amount": 1000.0, "xrp_value": 990.0}],
            asks=[{"price": 1.0, "token_amount": 1000.0, "xrp_value": 1000.0}],
        )
        out = simulate_entry_buy(
            asks=[{"price": 1.0, "token_amount": 1000.0, "xrp_value": 1000.0}],
            best_bid=0.99,
            best_ask=1.0,
            requested_size_xrp=50.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
        )
        eng = PnLAttributionEngine()
        exec_row = eng.create_execution_record(
            session,
            token_id=token.id,
            signal_id=sig.id,
            risk_decision_id=None,
            snapshot_id=entry_snap.id,
            position_id=None,
            side="BUY",
            execution_result=out,
            snapshot_time=now,
            signal_time=now,
            execution_time=now,
        )
        pos = eng.create_position_from_entry(
            session,
            token_id=token.id,
            issuer=token.issuer,
            currency=token.currency,
            signal_id=sig.id,
            risk_decision_id=None,
            execution_record_id=exec_row.id,
            snapshot_id=entry_snap.id,
            execution_result=out,
            alpha_signal=None,
            execution_time=now,
        )
        assert pos is not None
        pos.status = "PARTIAL_EXIT"
        session.add(pos)
        session.commit()

        _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[],
            asks=[{"price": 1.2, "token_amount": 1000.0, "xrp_value": 1200.0}],
        )
        latest = session.exec(select(MarketSnapshot).where(MarketSnapshot.token_id == token.id).order_by(MarketSnapshot.id.desc())).first()
        eng.update_positions_for_snapshot(
            session,
            token_id=token.id,
            snapshot=latest,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
            min_exit_retry_ms=0,
            max_exit_retries=5,
            approve_exit_fn=lambda p, s: True,
        )
        refreshed = session.get(Position, pos.position_id)

    assert refreshed is not None
    assert refreshed.status == "EXIT_FAILED_TRANSIENT"


def test_pnl_uses_filled_size_only() -> None:
    reset_tables()
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        session.add(
            Position(
                issuer=token.issuer,
                currency=token.currency,
                token_id=token.id,
                signal_id=sig.id,
                entry_vwap=1.0,
                entry_filled_size=10.0,
                remaining_size=0.0,
                entry_orderbook_snapshot_id=1,
                status="CLOSED",
            )
        )
        session.commit()
        pos = session.exec(select(Position).order_by(Position.created_at.desc())).first()
        session.add(
            PositionExitFill(
                position_id=pos.position_id,
                execution_id=None,
                snapshot_id=None,
                exit_vwap=1.2,
                fill_size=10.0,
                pnl_xrp=(1.2 - 1.0) * 10.0,
            )
        )
        session.commit()
        realized = PnLAttributionEngine().realized_pnl_summary(session)

    assert realized["realized_pnl_xrp"] == pytest.approx(2.0)


def test_multi_exit_aggregation_correctness() -> None:
    reset_tables()
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        pos = Position(
            issuer=token.issuer,
            currency=token.currency,
            token_id=token.id,
            signal_id=sig.id,
            entry_vwap=1.0,
            entry_filled_size=100.0,
            remaining_size=0.0,
            entry_orderbook_snapshot_id=1,
            status="CLOSED",
        )
        session.add(pos)
        session.commit()
        session.refresh(pos)

        session.add(PositionExitFill(position_id=pos.position_id, exit_vwap=1.1, fill_size=40.0, pnl_xrp=4.0))
        session.add(PositionExitFill(position_id=pos.position_id, exit_vwap=0.9, fill_size=60.0, pnl_xrp=-6.0))
        session.commit()

        realized = PnLAttributionEngine().realized_pnl_summary(session)

    assert realized["realized_pnl_xrp"] == pytest.approx(-2.0)


def test_unrealized_uses_bid_side_only() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        pos = Position(
            issuer=token.issuer,
            currency=token.currency,
            token_id=token.id,
            signal_id=sig.id,
            entry_vwap=1.0,
            entry_filled_size=50.0,
            remaining_size=50.0,
            entry_orderbook_snapshot_id=1,
            status="OPEN",
        )
        session.add(pos)
        session.commit()
        session.refresh(pos)

        snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 0.8, "token_amount": 200.0, "xrp_value": 160.0}],
            asks=[{"price": 1.5, "token_amount": 200.0, "xrp_value": 300.0}],
        )
        out = PnLAttributionEngine().simulate_unrealized_for_position(
            session,
            position=pos,
            snapshot=snap,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
        )

    assert out["unrealized_exit_vwap"] == pytest.approx(0.8)
    assert out["unrealized_pnl"] == pytest.approx((0.8 - 1.0) * 50.0)


def test_zero_liquidity_token_behavior() -> None:
    reset_tables()
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        pos = Position(
            issuer=token.issuer,
            currency=token.currency,
            token_id=token.id,
            signal_id=sig.id,
            entry_vwap=1.0,
            entry_filled_size=50.0,
            remaining_size=50.0,
            entry_orderbook_snapshot_id=1,
            status="OPEN",
        )
        session.add(pos)
        session.commit()

        # Snapshot without bids means no fillable exit.
        _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[],
            asks=[{"price": 1.2, "token_amount": 10.0, "xrp_value": 12.0}],
        )
        summary = PnLAttributionEngine().unrealized_pnl_summary(
            session,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
        )

    assert summary["unrealized_pnl_xrp"] is None


def test_failed_exit_retry_works() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        pos = Position(
            issuer=token.issuer,
            currency=token.currency,
            token_id=token.id,
            signal_id=sig.id,
            entry_vwap=1.0,
            entry_filled_size=50.0,
            exit_filled_size=0.0,
            remaining_size=50.0,
            entry_orderbook_snapshot_id=1,
            status="EXIT_FAILED_TRANSIENT",
            exit_attempt_count=1,
            last_exit_attempt_time=now - timedelta(seconds=30),
        )
        session.add(pos)
        session.commit()

        snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.1, "token_amount": 1000.0, "xrp_value": 1100.0}],
            asks=[{"price": 1.2, "token_amount": 1000.0, "xrp_value": 1200.0}],
        )
        eng = PnLAttributionEngine()
        eng.update_positions_for_snapshot(
            session,
            token_id=token.id,
            snapshot=snap,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
            min_exit_retry_ms=1000,
            max_exit_retries=5,
            approve_exit_fn=lambda p, s: True,
        )
        refreshed = session.get(Position, pos.position_id)

    assert refreshed is not None
    assert refreshed.status in {"PARTIAL_EXIT", "CLOSED"}


def test_exit_failed_permanent_not_retried() -> None:
    reset_tables()
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        pos = Position(
            issuer=token.issuer,
            currency=token.currency,
            token_id=token.id,
            signal_id=sig.id,
            entry_vwap=1.0,
            entry_filled_size=50.0,
            remaining_size=50.0,
            entry_orderbook_snapshot_id=1,
            status="EXIT_FAILED_PERMANENT",
            exit_attempt_count=3,
        )
        session.add(pos)
        session.commit()

        snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.2, "token_amount": 1000.0, "xrp_value": 1200.0}],
            asks=[{"price": 1.3, "token_amount": 1000.0, "xrp_value": 1300.0}],
        )
        before_attempts = pos.exit_attempt_count
        PnLAttributionEngine().update_positions_for_snapshot(
            session,
            token_id=token.id,
            snapshot=snap,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
            min_exit_retry_ms=1000,
            max_exit_retries=5,
            approve_exit_fn=lambda p, s: True,
        )
        refreshed = session.get(Position, pos.position_id)

    assert refreshed is not None
    assert refreshed.exit_attempt_count == before_attempts
    assert refreshed.status == "EXIT_FAILED_PERMANENT"


def test_no_auto_exit_without_decision() -> None:
    reset_tables()
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        pos = Position(
            issuer=token.issuer,
            currency=token.currency,
            token_id=token.id,
            signal_id=sig.id,
            entry_vwap=1.0,
            entry_filled_size=20.0,
            remaining_size=20.0,
            entry_orderbook_snapshot_id=1,
            status="OPEN",
        )
        session.add(pos)
        session.commit()

        snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.2, "token_amount": 1000.0, "xrp_value": 1200.0}],
            asks=[{"price": 1.3, "token_amount": 1000.0, "xrp_value": 1300.0}],
        )
        PnLAttributionEngine().update_positions_for_snapshot(
            session,
            token_id=token.id,
            snapshot=snap,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
            min_exit_retry_ms=1000,
            max_exit_retries=5,
            approve_exit_fn=lambda p, s: True,
        )
        refreshed = session.get(Position, pos.position_id)
        fills = session.exec(select(PositionExitFill).where(PositionExitFill.position_id == pos.position_id)).all()

    assert refreshed is not None
    assert refreshed.status == "OPEN"
    assert len(fills) == 0


def test_slippage_uses_top_of_book_not_midpoint() -> None:
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=[
            {"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0},
            {"price": 1.4, "token_amount": 100.0, "xrp_value": 140.0},
        ],
        best_bid=0.5,
        best_ask=1.0,
        requested_size_xrp=200.0,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1500,
        liquidity_haircut_pct=0.0,
    )
    assert out.avg_entry_price is not None
    assert out.slippage_pct == pytest.approx(((out.avg_entry_price - 1.0) / 1.0) * 100.0)


def test_time_invariant_violation_is_rejected() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.0, "token_amount": 100.0, "xrp_value": 100.0}],
            asks=[{"price": 1.1, "token_amount": 100.0, "xrp_value": 110.0}],
        )
        out = simulate_entry_buy(
            asks=[{"price": 1.1, "token_amount": 100.0, "xrp_value": 110.0}],
            best_bid=1.0,
            best_ask=1.1,
            requested_size_xrp=10.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
        )
        with pytest.raises(ValueError, match="FAILED_INVALID_TIMING"):
            PnLAttributionEngine().create_execution_record(
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
                execution_time=now - timedelta(milliseconds=1),
            )


def test_overfill_prevention() -> None:
    reset_tables()
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        pos = Position(
            issuer=token.issuer,
            currency=token.currency,
            token_id=token.id,
            signal_id=sig.id,
            entry_vwap=1.0,
            entry_filled_size=10.0,
            exit_filled_size=9.5,
            remaining_size=2.0,
            entry_orderbook_snapshot_id=1,
            status="PARTIAL_EXIT",
        )
        session.add(pos)
        session.commit()

        snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.2, "token_amount": 5.0, "xrp_value": 6.0}],
            asks=[{"price": 1.3, "token_amount": 100.0, "xrp_value": 130.0}],
        )

        with pytest.raises(ValueError, match="CRITICAL_OVERFILL_DETECTED"):
            PnLAttributionEngine().update_positions_for_snapshot(
                session,
                token_id=token.id,
                snapshot=snap,
                execution_latency_ms=0,
                max_snapshot_age_ms=1500,
                liquidity_haircut_pct=0.0,
                min_exit_retry_ms=0,
                max_exit_retries=5,
                approve_exit_fn=lambda p, s: True,
            )


def test_retry_uses_new_snapshot_not_old() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        pos = Position(
            issuer=token.issuer,
            currency=token.currency,
            token_id=token.id,
            signal_id=sig.id,
            entry_vwap=1.0,
            entry_filled_size=10.0,
            remaining_size=10.0,
            entry_orderbook_snapshot_id=1,
            status="EXIT_FAILED_TRANSIENT",
            last_exit_attempt_time=now - timedelta(seconds=10),
            exit_attempt_count=1,
        )
        session.add(pos)
        session.commit()

        old_snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[],
            asks=[{"price": 1.3, "token_amount": 100.0, "xrp_value": 130.0}],
        )
        new_snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.1, "token_amount": 100.0, "xrp_value": 110.0}],
            asks=[{"price": 1.2, "token_amount": 100.0, "xrp_value": 120.0}],
        )
        new_snap_id = new_snap.id

        eng = PnLAttributionEngine()
        eng.update_positions_for_snapshot(
            session,
            token_id=token.id,
            snapshot=new_snap,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
            min_exit_retry_ms=1000,
            max_exit_retries=5,
            approve_exit_fn=lambda p, s: True,
        )
        refreshed = session.get(Position, pos.position_id)

    assert refreshed is not None
    assert refreshed.exit_orderbook_snapshot_id == new_snap_id


def test_fill_levels_json_persisted_as_structured_list() -> None:
    reset_tables()
    now = datetime.now(tz=timezone.utc)
    with Session(engine) as session:
        token, sig = _mk_token_signal(session)
        snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.0, "token_amount": 300.0, "xrp_value": 300.0}],
            asks=[
                {"price": 1.01, "token_amount": 200.0, "xrp_value": 202.0},
                {"price": 1.02, "token_amount": 200.0, "xrp_value": 204.0},
            ],
        )
        out = simulate_entry_buy(
            asks=[
                {"price": 1.01, "token_amount": 200.0, "xrp_value": 202.0},
                {"price": 1.02, "token_amount": 200.0, "xrp_value": 204.0},
            ],
            best_bid=1.0,
            best_ask=1.01,
            requested_size_xrp=300.0,
            snapshot_time=now,
            signal_time=now,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
        )
        eng = PnLAttributionEngine()
        exec_row = eng.create_execution_record(
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
        )
        pos = eng.create_position_from_entry(
            session,
            token_id=token.id,
            issuer=token.issuer,
            currency=token.currency,
            signal_id=sig.id,
            risk_decision_id=None,
            execution_record_id=exec_row.id,
            snapshot_id=snap.id,
            execution_result=out,
            alpha_signal=None,
            execution_time=now,
        )
        assert pos is not None
        pos.status = "PARTIAL_EXIT"
        session.add(pos)
        session.commit()

        exit_snap = _mk_snapshot_with_depth(
            session,
            token.id,
            bids=[{"price": 1.03, "token_amount": 1000.0, "xrp_value": 1030.0}],
            asks=[{"price": 1.04, "token_amount": 1000.0, "xrp_value": 1040.0}],
        )
        eng.update_positions_for_snapshot(
            session,
            token_id=token.id,
            snapshot=exit_snap,
            execution_latency_ms=0,
            max_snapshot_age_ms=1500,
            liquidity_haircut_pct=0.0,
            min_exit_retry_ms=0,
            max_exit_retries=5,
            approve_exit_fn=lambda p, s: True,
        )

        exec_saved = session.get(ExecutionRecord, exec_row.id)
        exit_fill = session.exec(
            select(PositionExitFill)
            .where(PositionExitFill.position_id == pos.position_id)
            .order_by(PositionExitFill.id.desc())
        ).first()

    assert exec_saved is not None
    assert isinstance(exec_saved.fill_levels_json, list)
    assert len(exec_saved.fill_levels_json) >= 1
    assert isinstance(exec_saved.fill_levels_json[0], dict)

    assert exit_fill is not None
    assert isinstance(exit_fill.fill_levels_json, list)
    assert len(exit_fill.fill_levels_json) >= 1
    assert isinstance(exit_fill.fill_levels_json[0], dict)
