"""FastAPI application entry point."""

from __future__ import annotations

import contextlib

import uvicorn
from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.config import settings
from app.db.session import create_db_and_tables
from app.telemetry import get_logger

logger = get_logger("main")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Sonic XRPL Autotrader starting",
        bot_mode=settings.bot_mode,
        live_trading_enabled=settings.live_trading_enabled,
    )
    create_db_and_tables()
    yield
    logger.info("Sonic XRPL Autotrader shutting down")


app = FastAPI(
    title="Sonic XRPL Autotrader",
    version="0.1.0",
    description="Production-quality XRPL automated trading system",
    lifespan=lifespan,
)

app.include_router(health_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
