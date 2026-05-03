"""Orderbook snapshot builder — Phase 47.

Reads orderbook data from fixture store. No live calls. No order simulation.
"""

from __future__ import annotations

import hashlib
from typing import Any

from sonic_xrpl.market.models import OfferEntry, OrderbookSnapshot


def _orderbook_id(taker_gets: Any, taker_pays: Any) -> str:
    """Deterministic orderbook snapshot ID."""
    raw = f"{taker_gets}|{taker_pays}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _normalise_asset(raw: Any) -> str:
    """Normalise taker_gets/taker_pays to canonical key string.

    XRP string → "XRP"
    IOU dict → "USD:rIssuer..."
    """
    if isinstance(raw, str):
        return "XRP"
    if isinstance(raw, dict):
        currency = raw.get("currency", "")
        issuer = raw.get("issuer", "")
        if currency and issuer:
            return f"{currency}:{issuer}"
        return currency or str(raw)
    return str(raw)


def _extract_quality(offer: dict[str, Any]) -> str | None:
    """Extract quality value from an offer."""
    q = offer.get("quality")
    return str(q) if q is not None else None


def _sort_offers(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort offers by quality ascending (best bid first in price terms)."""
    def _quality_float(o: dict[str, Any]) -> float:
        try:
            return float(o.get("quality", 0))
        except (TypeError, ValueError):
            return 0.0

    return sorted(offers, key=_quality_float)


def _compute_spread_bps(best_bid_quality: float | None, best_ask_quality: float | None) -> float | None:
    """Compute bid-ask spread in basis points.

    For XRPL orderbook:
    - best_bid: lowest quality (most offers to sell base)
    - spread_bps = (ask - bid) / mid * 10_000
    """
    if best_bid_quality is None or best_ask_quality is None:
        return None
    if best_bid_quality <= 0 or best_ask_quality <= 0:
        return None
    mid = (best_bid_quality + best_ask_quality) / 2.0
    if mid <= 0:
        return None
    return abs(best_ask_quality - best_bid_quality) / mid * 10_000.0


def _depth_summary(offers: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute a simple depth summary from offers."""
    return {
        "offer_count": len(offers),
        "has_data": len(offers) > 0,
    }


def build_orderbook_snapshot(
    raw_orderbook: dict[str, Any],
    ledger_index: int,
) -> OrderbookSnapshot:
    """Build an OrderbookSnapshot from raw book_offers fixture data."""
    limitations: list[str] = []

    taker_gets_raw = raw_orderbook.get("taker_gets", "XRP")
    taker_pays_raw = raw_orderbook.get("taker_pays", {})
    taker_gets_key = _normalise_asset(taker_gets_raw)
    taker_pays_key = _normalise_asset(taker_pays_raw)

    raw_offers: list[dict[str, Any]] = raw_orderbook.get("offers", [])

    if not raw_offers:
        limitations.append("orderbook is empty — no offers in fixture")

    sorted_offers = _sort_offers(raw_offers)

    offer_entries: list[OfferEntry] = []
    for o in sorted_offers:
        offer_entries.append(OfferEntry(
            account=o.get("account", ""),
            taker_gets=o.get("taker_gets"),
            taker_pays=o.get("taker_pays"),
            quality=_extract_quality(o),
        ))

    best_bid_quality: float | None = None
    best_ask_quality: float | None = None
    best_bid: str | None = None
    best_ask: str | None = None

    if sorted_offers:
        try:
            best_bid_quality = float(sorted_offers[0].get("quality", 0))
            best_bid = str(best_bid_quality)
        except (TypeError, ValueError):
            limitations.append("could not parse best bid quality")

        if len(sorted_offers) > 1:
            try:
                best_ask_quality = float(sorted_offers[-1].get("quality", 0))
                best_ask = str(best_ask_quality)
            except (TypeError, ValueError):
                limitations.append("could not parse best ask quality")
        else:
            limitations.append("only one offer — cannot compute spread")

    spread_bps = _compute_spread_bps(best_bid_quality, best_ask_quality)
    if spread_bps is None and raw_offers:
        limitations.append("spread_bps could not be computed from available offers")

    ob_id = _orderbook_id(taker_gets_key, taker_pays_key)

    return OrderbookSnapshot(
        orderbook_id=ob_id,
        taker_gets=taker_gets_key,
        taker_pays=taker_pays_key,
        offers=offer_entries,
        best_bid=best_bid,
        best_ask=best_ask,
        spread_bps=spread_bps,
        depth_summary=_depth_summary(raw_offers),
        ledger_index=ledger_index,
        limitations=limitations,
    )
