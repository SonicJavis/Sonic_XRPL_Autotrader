from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float:
    if isinstance(value, dict):
        return float(value.get("value", 0.0))
    return float(value)


def parse_orderbook(offers: list[dict[str, Any]]) -> dict[str, Any]:
    bids: list[dict[str, float]] = []
    asks: list[dict[str, float]] = []

    for offer in offers:
        gets = _to_float(offer.get("taker_gets", 0.0))
        pays = _to_float(offer.get("taker_pays", 0.0))
        if gets <= 0 or pays <= 0:
            continue

        side = str(offer.get("side", "ask")).lower()
        if side == "bid":
            xrp_amount = gets
            token_amount = pays
        else:
            token_amount = gets
            xrp_amount = pays

        if token_amount <= 0:
            continue

        price_xrp_per_token = xrp_amount / token_amount
        level = {"price": price_xrp_per_token, "token_amount": token_amount, "xrp_value": xrp_amount}

        if side == "bid":
            bids.append(level)
        else:
            asks.append(level)

    bids.sort(key=lambda row: row["price"], reverse=True)
    asks.sort(key=lambda row: row["price"])

    return {
        "bids": bids,
        "asks": asks,
        "best_bid": bids[0] if bids else None,
        "best_ask": asks[0] if asks else None,
    }
