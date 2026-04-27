from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    container = request.app.state.container
    xrpl_health = container.xrpl_client.health_check()
    return {"status": "ok", "xrpl": xrpl_health}
