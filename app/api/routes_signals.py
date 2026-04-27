from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlmodel import select

from app.db.models import Signal, Token
from app.market_data.token_registry import RegisteredToken

router = APIRouter()


class RegisterTokenRequest(BaseModel):
    issuer: str
    currency: str
    symbol: str
    source: str = "manual"


@router.get("/signals")
def list_signals(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(Signal).order_by(Signal.id.desc()).limit(50)).all()
    return [row.model_dump() for row in rows]


@router.post("/tokens/register")
def register_token(payload: RegisterTokenRequest, request: Request) -> dict[str, object]:
    container = request.app.state.container

    token = RegisteredToken(
        issuer=payload.issuer,
        currency=payload.currency,
        symbol=payload.symbol,
        source=payload.source,
    )
    container.token_registry.register(token)

    with container.session_factory() as session:
        row = Token(**payload.model_dump())
        session.add(row)
        session.commit()
        session.refresh(row)

    return {"ok": True, "token_id": row.id}


@router.post("/pipeline/run-once")
def run_pipeline_once(request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        return container.pipeline.run_once(session=session)
