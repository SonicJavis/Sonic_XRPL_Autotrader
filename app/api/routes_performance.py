from __future__ import annotations

from fastapi import APIRouter, Request

from app.alpha.performance_engine import PerformanceEngine

router = APIRouter()


@router.get("/performance/summary")
def performance_summary(request: Request, limit: int = 200) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PerformanceEngine(container.settings)
        return engine.summary(session, limit=limit)


@router.get("/performance/trades")
def performance_trades(request: Request, limit: int = 200) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PerformanceEngine(container.settings)
        return engine.trades(session, limit=limit)


@router.get("/performance/alpha-breakdown")
def performance_alpha_breakdown(request: Request, limit: int = 300) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PerformanceEngine(container.settings)
        return engine.alpha_breakdown(session, limit=limit)
