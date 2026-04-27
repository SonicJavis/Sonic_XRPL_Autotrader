from __future__ import annotations

from fastapi import APIRouter, Request
from sqlmodel import select

from app.db.models import MarketSnapshot, WatchedToken
from app.market_data.snapshot_builder import build_snapshot_from_offers

router = APIRouter()


@router.get("/market/snapshots")
def list_market_snapshots(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(MarketSnapshot).order_by(MarketSnapshot.id.desc()).limit(100)).all()
    return [row.model_dump() for row in rows]


@router.get("/market/orderbook")
def market_orderbook(request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        token = session.exec(select(WatchedToken).where(WatchedToken.is_active == True).order_by(WatchedToken.id.asc())).first()

    if token is None:
        return {"ok": False, "reason": "no watched token"}

    book = container.pipeline._fetch_orderbook(token)
    snapshot = build_snapshot_from_offers(book.get("offers", []))

    return {
        "ok": True,
        "token": {"issuer": token.issuer, "currency": token.currency, "is_xrp": token.is_xrp},
        "best_bid": snapshot["parsed"]["best_bid"],
        "best_ask": snapshot["parsed"]["best_ask"],
        "order_count": snapshot["order_count"],
        "bids": snapshot["parsed"]["bids"][:10],
        "asks": snapshot["parsed"]["asks"][:10],
    }
