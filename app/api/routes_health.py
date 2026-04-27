"""FastAPI health routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.risk.kill_switch import is_kill_switch_active

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """System health check."""
    return {
        "status": "ok",
        "bot_mode": settings.bot_mode,
        "live_trading_enabled": settings.live_trading_enabled,
        "kill_switch_active": is_kill_switch_active(),
    }


@router.get("/health/config")
def health_config() -> dict:
    """Expose non-sensitive configuration values."""
    return {
        "bot_mode": settings.bot_mode,
        "xrpl_rpc_url": settings.xrpl_rpc_url,
        "max_trade_xrp": settings.max_trade_xrp,
        "max_open_positions": settings.max_open_positions,
        "paper_stop_loss_pct": settings.paper_stop_loss_pct,
        "paper_take_profit_pct": settings.paper_take_profit_pct,
    }
