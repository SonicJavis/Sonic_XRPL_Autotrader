from __future__ import annotations

from contextlib import contextmanager

from fastapi import FastAPI
from sqlmodel import Session

from app.api.routes_health import router as health_router
from app.api.routes_market import router as market_router
from app.api.routes_mode import router as mode_router
from app.api.routes_signals import router as signals_router
from app.api.routes_trades import router as trades_router
from app.config import Settings
from app.db.session import engine, init_db
from app.execution.paper import PaperExecutor
from app.execution.pipeline import ExecutionPipeline
from app.market_data.token_registry import TokenRegistry
from app.risk.kill_switch import KillSwitch
from app.risk.risk_manager import RiskManager
from app.strategies.new_token_scanner import NewTokenScannerStrategy
from app.strategies.strategy_registry import StrategyRegistry
from app.xrpl_core.client import XRPLReadOnlyClient


class AppContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.xrpl_client = XRPLReadOnlyClient(settings.XRPL_RPC_URL)
        self.token_registry = TokenRegistry()
        self.kill_switch = KillSwitch()
        self.strategy_registry = StrategyRegistry()
        self.strategy_registry.register(NewTokenScannerStrategy(settings=settings))
        self.risk_manager = RiskManager(settings, self.kill_switch)
        self.paper_executor = PaperExecutor(settings)
        self.pipeline = ExecutionPipeline(
            settings,
            self.xrpl_client,
            self.strategy_registry,
            self.risk_manager,
            self.paper_executor,
        )

    @contextmanager
    def session_factory(self):
        with Session(engine) as session:
            yield session


def create_app() -> FastAPI:
    settings = Settings()
    init_db()

    app = FastAPI(title="Sonic XRPL Autotrader API", version="0.2.0")
    app.state.container = AppContainer(settings)

    app.include_router(health_router)
    app.include_router(market_router)
    app.include_router(mode_router)
    app.include_router(signals_router)
    app.include_router(trades_router)
    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = Settings()
    host = "0.0.0.0" if settings.ALLOW_REMOTE_ACCESS else "127.0.0.1"
    uvicorn.run("app.main:app", host=host, port=8000, reload=False)


if __name__ == "__main__":
    main()
