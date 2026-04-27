from __future__ import annotations

import logging
from statistics import median
from typing import Any

from app.market_data.normalization import normalize_amount

logger = logging.getLogger("sonic.market_data.orderbook")


def _to_float(value: Any) -> float:
    return normalize_amount(value)


def _is_price_outlier(price: float, med: float) -> bool:
    if med <= 0:
        return True
    if price > med * 5:
        return True
    if price < med * 0.2:
        return True
    return False


def _quality_deviation_pct(price: float, quality: float) -> float:
    if quality <= 0 or price <= 0:
        return 0.0
    direct = abs(price - quality) / quality * 100.0
    inverse = abs(price - (1.0 / quality)) / (1.0 / quality) * 100.0
    return min(direct, inverse)


def parse_orderbook(offers: list[dict[str, Any]]) -> dict[str, Any]:
    raw_offer_count = len(offers)
    bids: list[dict[str, float]] = []
    asks: list[dict[str, float]] = []
    rejected_orders = 0
    price_deviation_warnings = 0
    prefilter_levels: list[dict[str, float | str]] = []

    for offer in offers:
        try:
            gets = _to_float(offer.get("taker_gets", 0.0))
            pays = _to_float(offer.get("taker_pays", 0.0))
        except Exception:
            rejected_orders += 1
            continue

        if gets <= 0 or pays <= 0:
            rejected_orders += 1
            continue

        side = str(offer.get("side", "ask")).lower()
        if side not in {"bid", "ask"}:
            rejected_orders += 1
            continue

        if side == "bid":
            xrp_amount = gets
            token_amount = pays
        else:
            token_amount = gets
            xrp_amount = pays

        if token_amount <= 0:
            rejected_orders += 1
            continue

        price_xrp_per_token = xrp_amount / token_amount
        if price_xrp_per_token <= 0 or xrp_amount < 0.01:
            rejected_orders += 1
            continue

        quality = float(offer.get("quality", 0.0))
        deviation_pct = _quality_deviation_pct(price_xrp_per_token, quality) if quality > 0 else 0.0
        if deviation_pct > 5.0:
            price_deviation_warnings += 1
            logger.warning(
                "Orderbook price-quality deviation above threshold",
                extra={
                    "event_type": "orderbook_quality_deviation",
                    "price": price_xrp_per_token,
                    "quality": quality,
                    "deviation_pct": deviation_pct,
                },
            )

        prefilter_levels.append(
            {
                "side": side,
                "price": price_xrp_per_token,
                "token_amount": token_amount,
                "xrp_value": xrp_amount,
            }
        )

    prices = [float(row["price"]) for row in prefilter_levels]
    med = median(prices) if prices else 0.0

    for row in prefilter_levels:
        price = float(row["price"])
        if _is_price_outlier(price, med):
            rejected_orders += 1
            continue

        level = {
            "price": price,
            "token_amount": float(row["token_amount"]),
            "xrp_value": float(row["xrp_value"]),
        }

        if row["side"] == "bid":
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
        "raw_offer_count": raw_offer_count,
        "filtered_offer_count": len(bids) + len(asks),
        "rejected_orders": rejected_orders,
        "price_deviation_warnings": price_deviation_warnings,
    }
