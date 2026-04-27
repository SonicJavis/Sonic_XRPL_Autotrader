from sqlmodel import Session, select

from app.config import Settings
from app.db.models import RiskEvent, Signal
from app.db.session import engine, init_db
from app.execution.paper import PaperExecutor
from app.execution.pipeline import ExecutionPipeline
from app.market_data.token_registry import RegisteredToken, TokenRegistry
from app.risk.kill_switch import KillSwitch
from app.risk.risk_manager import RiskManager
from app.strategies.new_token_scanner import NewTokenScannerStrategy
from app.strategies.strategy_registry import StrategyRegistry


def reset_tables() -> None:
    Signal.__table__.drop(engine, checkfirst=True)
    RiskEvent.__table__.drop(engine, checkfirst=True)
    init_db()


def build_pipeline(settings: Settings, registry: TokenRegistry) -> ExecutionPipeline:
    strategy_registry = StrategyRegistry()
    strategy_registry.register(NewTokenScannerStrategy(registry))
    risk_manager = RiskManager(settings, KillSwitch())
    paper_executor = PaperExecutor(settings)
    return ExecutionPipeline(settings, strategy_registry, risk_manager, paper_executor)


def test_pipeline_stores_signals() -> None:
    reset_tables()
    settings = Settings(MAX_TRADE_XRP=5)
    registry = TokenRegistry()
    registry.register(RegisteredToken(issuer="rIssuer", currency="USD", symbol="TOK"))

    pipeline = build_pipeline(settings, registry)

    with Session(engine) as session:
        result = pipeline.run_once(session)
        stored_signals = session.exec(select(Signal)).all()

    assert result["signals"] >= 1
    assert len(stored_signals) >= 1


def test_pipeline_stores_risk_denials() -> None:
    reset_tables()
    settings = Settings(MAX_TRADE_XRP=0.1)
    registry = TokenRegistry()
    registry.register(RegisteredToken(issuer="rIssuer", currency="USD", symbol="TOK"))

    pipeline = build_pipeline(settings, registry)

    with Session(engine) as session:
        pipeline.run_once(session)
        denials = session.exec(select(RiskEvent)).all()

    assert len(denials) >= 1
