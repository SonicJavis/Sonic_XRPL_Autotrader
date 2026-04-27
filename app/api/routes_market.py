from __future__ import annotations

from fastapi import APIRouter, Request
from sqlmodel import select

from app.db.models import AlphaSignal, MarketDepthLevel, MarketSnapshot, RiskDecisionRecord, WatchedToken
from app.market_data.snapshot_builder import build_snapshot_from_offers

router = APIRouter()


@router.get("/market/snapshots")
def list_market_snapshots(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(MarketSnapshot).order_by(MarketSnapshot.id.desc()).limit(100)).all()
    return [row.model_dump() for row in rows]


@router.get("/signals/alpha")
def list_alpha_signals(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(AlphaSignal).order_by(AlphaSignal.id.desc()).limit(100)).all()
    return [row.model_dump() for row in rows]


@router.get("/risk/decisions")
def list_risk_decisions(request: Request) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        rows = session.exec(select(RiskDecisionRecord).order_by(RiskDecisionRecord.id.desc()).limit(100)).all()
    return [row.model_dump() for row in rows]


@router.get("/market/depth")
def market_depth(request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        latest = session.exec(select(MarketSnapshot).order_by(MarketSnapshot.id.desc())).first()
        if latest is None or latest.id is None:
            return {"ok": False, "reason": "no market snapshots"}
        levels = session.exec(
            select(MarketDepthLevel).where(MarketDepthLevel.snapshot_id == latest.id).order_by(
                MarketDepthLevel.side.asc(), MarketDepthLevel.level_index.asc()
            )
        ).all()

    bids = [row.model_dump() for row in levels if row.side == "bid"]
    asks = [row.model_dump() for row in levels if row.side == "ask"]
    return {
        "ok": True,
        "snapshot_id": latest.id,
        "bids": bids,
        "asks": asks,
    }


@router.get("/market/history")
def market_history(request: Request, token_id: int | None = None, limit: int = 50) -> list[dict[str, object]]:
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 200)

    with container.session_factory() as session:
        query = select(MarketSnapshot).order_by(MarketSnapshot.id.desc())
        if token_id is not None:
            query = query.where(MarketSnapshot.token_id == token_id)
        rows = session.exec(query.limit(safe_limit)).all()

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
        "valid": snapshot["valid"],
        "invalid_reasons": snapshot["invalid_reasons"],
        "best_bid": snapshot["parsed"]["best_bid"],
        "best_ask": snapshot["parsed"]["best_ask"],
        "price_xrp": snapshot["price_xrp"],
        "spread_pct": snapshot["spread_pct"],
        "liquidity_xrp": snapshot["liquidity_xrp"],
        "liquidity_bid_xrp": snapshot["liquidity_bid_xrp"],
        "liquidity_ask_xrp": snapshot["liquidity_ask_xrp"],
        "order_count": snapshot["order_count"],
        "raw_offer_count": snapshot["raw_offer_count"],
        "filtered_offer_count": snapshot["filtered_offer_count"],
        "rejected_orders": snapshot["rejected_orders"],
        "price_deviation_warnings": snapshot["price_deviation_warnings"],
        "bids": snapshot["parsed"]["bids"][:10],
        "asks": snapshot["parsed"]["asks"][:10],
    }
