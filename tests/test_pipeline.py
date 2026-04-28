from sqlmodel import Session, select

from app.alpha.engine import AlphaEngine
from app.config import Settings
from app.db.models import AlphaCooldownRecord, AlphaSignal, ExecutionFillSlice, ExecutionRecord, MarketDepthLevel, MarketSnapshot, PaperTradeOutcome, Position, PositionExitFill, RiskDecisionRecord, RiskEvent, Signal, WatchedToken
from app.db.session import engine, init_db
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


def build_pipeline(settings: Settings) -> ExecutionPipeline:
    strategy_registry = StrategyRegistry()
    strategy_registry.register(NewTokenScannerStrategy(settings=settings))
    risk_manager = RiskManager(settings, KillSwitch())
    paper_executor = PaperExecutor(settings)
    alpha_engine = AlphaEngine(settings)
    return ExecutionPipeline(settings, FakeXRPLClient(), strategy_registry, risk_manager, paper_executor, alpha_engine)


def test_pipeline_stores_signals() -> None:
    reset_tables()
    settings = Settings(MAX_TRADE_XRP=5, MIN_LIQUIDITY_XRP=1, MAX_SPREAD_PCT=50)

    pipeline = build_pipeline(settings)

    with Session(engine) as session:
        session.add(WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False))
        session.commit()
        result = pipeline.run_once(session)
        stored_signals = session.exec(select(Signal)).all()
        snapshots = session.exec(select(MarketSnapshot)).all()

    assert result["signals"] >= 1
    assert len(stored_signals) >= 1
    assert len(snapshots) >= 1


def test_pipeline_stores_risk_denials() -> None:
    reset_tables()
    settings = Settings(MAX_TRADE_XRP=0.1, MAX_TOTAL_EXPOSURE_XRP=0.05, MIN_LIQUIDITY_XRP=1, MAX_SPREAD_PCT=50)

    pipeline = build_pipeline(settings)

    with Session(engine) as session:
        session.add(WatchedToken(issuer="rIssuer", currency="USD", is_xrp=False))
        session.commit()
        pipeline.run_once(session)
        denials = session.exec(select(RiskEvent)).all()

    assert len(denials) >= 1
