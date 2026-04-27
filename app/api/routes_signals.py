from __future__ import annotations

from datetime import datetime, timezone
import re

from fastapi import APIRouter, Request
from pydantic import BaseModel, field_validator
from sqlmodel import select

from app.db.models import Signal, WatchedToken
from app.market_data.token_registry import RegisteredToken

router = APIRouter()


class RegisterTokenRequest(BaseModel):
    issuer: str = ""
    currency: str

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        currency = value.strip().upper()
        if len(currency) == 0 or len(currency) > 40:
            raise ValueError("currency length must be between 1 and 40")
        return currency

    @field_validator("issuer")
    @classmethod
    def validate_issuer(cls, value: str) -> str:
        issuer = value.strip()
        if issuer and not re.fullmatch(r"r[1-9A-HJ-NP-Za-km-z]{24,34}", issuer):
            raise ValueError("issuer must be a valid XRPL address")
        return issuer


@router.get("/signals")
def list_signals(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(Signal).order_by(Signal.id.desc()).limit(50)).all()
    return [row.model_dump() for row in rows]


@router.post("/tokens/register")
def register_token(payload: RegisterTokenRequest, request: Request) -> dict[str, object]:
    container = request.app.state.container
    is_xrp = payload.currency == "XRP"
    issuer = "" if is_xrp else payload.issuer

    if not is_xrp and not issuer:
        return {"ok": False, "error": "issuer required for IOU token"}

    token = RegisteredToken(
        issuer=issuer,
        currency=payload.currency,
        symbol=payload.currency,
        is_xrp=is_xrp,
        source="manual",
    )
    container.token_registry.register(token)

    with container.session_factory() as session:
        existing = session.exec(
            select(WatchedToken).where(
                WatchedToken.issuer == issuer,
                WatchedToken.currency == payload.currency,
            )
        ).first()

        if existing is not None:
            existing.last_seen_at = datetime.now(tz=timezone.utc)
            existing.is_active = True
            row = existing
        else:
            row = WatchedToken(
                issuer=issuer,
                currency=payload.currency,
                is_xrp=is_xrp,
            )
            session.add(row)
        session.commit()
        session.refresh(row)

    return {"ok": True, "token_id": row.id}


@router.get("/tokens")
def list_tokens(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(WatchedToken).where(WatchedToken.is_active == True).order_by(WatchedToken.id.asc())).all()
    return [row.model_dump() for row in rows]


@router.post("/pipeline/run-once")
def run_pipeline_once(request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        return container.pipeline.run_once(session=session)
