from sqlmodel import Session

from app.config import Settings
from app.db.models import PaperTrade
from app.db.session import engine, init_db
from app.execution.paper import PaperExecutor
from app.strategies.base import SignalCandidate


def reset_tables() -> None:
    PaperTrade.__table__.drop(engine, checkfirst=True)
    init_db()


def test_paper_pnl_calculation_is_correct() -> None:
    pnl = PaperExecutor.calculate_pnl(side="BUY", entry_price_xrp=1.0, exit_price_xrp=1.2, size_xrp=10)
    assert pnl == 2.0


def test_open_and_close_trade() -> None:
    reset_tables()
    executor = PaperExecutor(Settings())
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
        opened = executor.open_trade(session, candidate, entry_price_xrp=1.0)
        closed = executor.close_trade(session, opened.id, exit_price_xrp=1.2)

    assert closed.status == "CLOSED"
    assert closed.pnl_xrp == 0.4
