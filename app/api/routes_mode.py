from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/mode")
def mode(request: Request) -> dict[str, object]:
    container = request.app.state.container
    settings = container.settings
    bind_host = "127.0.0.1" if not settings.ALLOW_REMOTE_ACCESS else "0.0.0.0"
    return {
        "bot_mode": settings.BOT_MODE,
        "live_trading_enabled": settings.LIVE_TRADING_ENABLED,
        "allow_remote_access": settings.ALLOW_REMOTE_ACCESS,
        "recommended_bind_host": bind_host,
        "kill_switch_engaged": container.kill_switch.is_engaged(),
    }


@router.post("/emergency-stop")
def emergency_stop(request: Request) -> dict[str, object]:
    container = request.app.state.container
    container.kill_switch.engage()
    return {"ok": True, "kill_switch_engaged": True}
