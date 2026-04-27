from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from app.db.models import ExecutionRecord, MarketSnapshot, Position
from app.execution.pnl_attribution_engine import PnLAttributionEngine

router = APIRouter()


@router.get("/positions")
def list_positions(request: Request, limit: int = 200) -> list[dict[str, object]]:
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 500)
    with container.session_factory() as session:
        rows = session.exec(select(Position).order_by(Position.entry_time.desc()).limit(safe_limit)).all()
    return [row.model_dump() for row in rows]


@router.get("/positions/{position_id}")
def get_position(position_id: str, request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        row = session.get(Position, position_id)
    if row is None:
        raise HTTPException(status_code=404, detail="position not found")
    return row.model_dump()


@router.get("/pnl/realized")
def pnl_realized(request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PnLAttributionEngine()
        return engine.realized_pnl_summary(session)


@router.get("/pnl/unrealized")
def pnl_unrealized(request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PnLAttributionEngine()
        return engine.unrealized_pnl_summary(
            session,
            execution_latency_ms=container.settings.EXECUTION_LATENCY_MS,
            max_snapshot_age_ms=container.settings.MAX_SNAPSHOT_AGE_MS,
            liquidity_haircut_pct=container.settings.EXECUTION_LIQUIDITY_HAIRCUT_PCT,
        )


@router.get("/failures")
def list_failures(request: Request, limit: int = 200) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PnLAttributionEngine()
        return engine.list_failures(session, limit=limit)


@router.get("/execution/{execution_id}")
def get_execution(execution_id: int, request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        row = session.get(ExecutionRecord, execution_id)
    if row is None:
        raise HTTPException(status_code=404, detail="execution not found")
    return row.model_dump()
