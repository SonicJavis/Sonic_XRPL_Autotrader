from __future__ import annotations

from fastapi import APIRouter, Request
from sqlmodel import select

from app.db.models import PaperTrade, RiskEvent

router = APIRouter()


@router.get("/paper-trades")
def list_paper_trades(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(PaperTrade).order_by(PaperTrade.id.desc()).limit(100)).all()
    return [row.model_dump() for row in rows]


@router.get("/risk/events")
def list_risk_events(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(RiskEvent).order_by(RiskEvent.id.desc()).limit(100)).all()
    return [row.model_dump() for row in rows]
