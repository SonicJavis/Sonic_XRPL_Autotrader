import pytest
from sqlmodel import Session, select

from app.config import Settings
from app.db.models import CapitalLedger, CapitalReservation, PaperTrade
from app.db.session import engine, init_db
from app.execution.paper import PaperExecutor
from app.strategies.base import SignalCandidate


def reset_tables() -> None:
    CapitalReservation.__table__.drop(engine, checkfirst=True)
    CapitalLedger.__table__.drop(engine, checkfirst=True)
    PaperTrade.__table__.drop(engine, checkfirst=True)
    init_db()


def test_paper_pnl_calculation_is_correct() -> None:
    pnl = PaperExecutor.calculate_pnl(side="BUY", entry_price_xrp=1.0, exit_price_xrp=1.2, size_xrp=10)
    assert pnl == 2.0


def test_open_and_close_trade() -> None:
    reset_tables()
    executor = PaperExecutor(Settings(STARTING_PAPER_BALANCE_XRP=100.0))
    candidate = SignalCandidate(
        strategy_name="test",
        issuer="rIssuer",
        currency="USD",
        side="BUY",
        confidence=0.8,
        risk_score=0.2,
        suggested_size_xrp=2.0,
        reason="test",
        invalidation_condition="none",
    )

    with Session(engine) as session:
        reservation = executor.reserve_capital(
            session,
            signal_id=1,
            issuer=candidate.issuer,
            currency=candidate.currency,
            requested_xrp=candidate.suggested_size_xrp,
        )
        settled = executor.settle_entry_fill(
            session,
            reservation_id=reservation.id,
            filled_xrp=2.0,
        )
        opened = executor.open_trade(
            session,
            candidate,
            entry_price_xrp=1.0,
            size_xrp=settled.deployed_xrp,
            reservation_id=settled.id,
        )
        closed = executor.close_trade(session, opened.id, exit_price_xrp=1.2)
        ledger = session.exec(select(CapitalLedger).order_by(CapitalLedger.id.asc())).first()

    assert closed.status == "CLOSED"
    assert closed.pnl_xrp == 0.4
    assert ledger is not None


def test_insufficient_capital_blocks_trade() -> None:
    reset_tables()
    executor = PaperExecutor(Settings(STARTING_PAPER_BALANCE_XRP=1.0, MAX_POSITION_XRP=5.0))

    with Session(engine) as session:
        with pytest.raises(ValueError, match="insufficient available capital"):
            executor.reserve_capital(
                session,
                signal_id=1,
                issuer="rIssuer",
                currency="USD",
                requested_xrp=2.0,
            )


def test_partial_fill_releases_excess_reserve() -> None:
    reset_tables()
    executor = PaperExecutor(Settings(STARTING_PAPER_BALANCE_XRP=100.0, MAX_POSITION_XRP=50.0))

    with Session(engine) as session:
        reservation = executor.reserve_capital(
            session,
            signal_id=1,
            issuer="rIssuer",
            currency="USD",
            requested_xrp=10.0,
        )
        settled = executor.settle_entry_fill(
            session,
            reservation_id=reservation.id,
            filled_xrp=4.0,
        )
        ledger = session.exec(select(CapitalLedger).order_by(CapitalLedger.id.asc())).first()

    assert settled.deployed_xrp == 4.0
    assert settled.released_xrp == 6.0
    assert settled.status == "DEPLOYED"
    assert ledger is not None
    assert ledger.available_balance_xrp == pytest.approx(96.0)
    assert ledger.locked_balance_xrp == pytest.approx(4.0)


def test_failed_trade_releases_all_capital() -> None:
    reset_tables()
    executor = PaperExecutor(Settings(STARTING_PAPER_BALANCE_XRP=100.0, MAX_POSITION_XRP=50.0))

    with Session(engine) as session:
        reservation = executor.reserve_capital(
            session,
            signal_id=2,
            issuer="rIssuer",
            currency="USD",
            requested_xrp=15.0,
        )
        settled = executor.settle_entry_fill(
            session,
            reservation_id=reservation.id,
            filled_xrp=0.0,
            failure_reason="NO_LIQUIDITY",
        )
        ledger = session.exec(select(CapitalLedger).order_by(CapitalLedger.id.asc())).first()

    assert settled.status == "RELEASED"
    assert settled.deployed_xrp == 0.0
    assert settled.released_xrp == 15.0
    assert ledger is not None
    assert ledger.available_balance_xrp == pytest.approx(100.0)
    assert ledger.locked_balance_xrp == pytest.approx(0.0)


def test_max_concurrent_positions_enforced() -> None:
    reset_tables()
    settings = Settings(
        STARTING_PAPER_BALANCE_XRP=100.0,
        MAX_POSITION_XRP=10.0,
        MAX_CONCURRENT_POSITIONS=1,
    )
    executor = PaperExecutor(settings)
    candidate = SignalCandidate(
        strategy_name="test",
        issuer="rIssuer",
        currency="USD",
        side="BUY",
        confidence=0.8,
        risk_score=0.2,
        suggested_size_xrp=5.0,
        reason="test",
        invalidation_condition="none",
    )

    with Session(engine) as session:
        first = executor.reserve_capital(
            session,
            signal_id=1,
            issuer=candidate.issuer,
            currency=candidate.currency,
            requested_xrp=5.0,
        )
        settled = executor.settle_entry_fill(session, reservation_id=first.id, filled_xrp=5.0)
        executor.open_trade(
            session,
            candidate,
            entry_price_xrp=1.0,
            size_xrp=settled.deployed_xrp,
            reservation_id=settled.id,
        )

        with pytest.raises(ValueError, match="max concurrent positions reached"):
            executor.reserve_capital(
                session,
                signal_id=2,
                issuer=candidate.issuer,
                currency=candidate.currency,
                requested_xrp=5.0,
            )


def test_capital_drift_never_occurs() -> None:
    reset_tables()
    settings = Settings(STARTING_PAPER_BALANCE_XRP=100.0, MAX_POSITION_XRP=20.0)
    executor = PaperExecutor(settings)
    candidate = SignalCandidate(
        strategy_name="test",
        issuer="rIssuer",
        currency="USD",
        side="BUY",
        confidence=0.8,
        risk_score=0.2,
        suggested_size_xrp=10.0,
        reason="test",
        invalidation_condition="none",
    )

    with Session(engine) as session:
        reservation = executor.reserve_capital(
            session,
            signal_id=3,
            issuer=candidate.issuer,
            currency=candidate.currency,
            requested_xrp=10.0,
        )
        settled = executor.settle_entry_fill(session, reservation_id=reservation.id, filled_xrp=7.0)
        trade = executor.open_trade(
            session,
            candidate,
            entry_price_xrp=1.0,
            size_xrp=settled.deployed_xrp,
            reservation_id=settled.id,
        )
        executor.close_trade(session, trade.id, exit_price_xrp=1.1)

        ledger = session.exec(select(CapitalLedger).order_by(CapitalLedger.id.asc())).first()

    assert ledger is not None
    assert ledger.available_balance_xrp >= 0.0
    assert ledger.locked_balance_xrp >= 0.0
    assert ledger.total_balance_xrp == pytest.approx(ledger.available_balance_xrp + ledger.locked_balance_xrp)
