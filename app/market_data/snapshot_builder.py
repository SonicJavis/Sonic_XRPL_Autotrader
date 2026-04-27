from __future__ import annotations

from statistics import median

from app.market_data.orderbook_parser import parse_orderbook


def _filtered_levels(levels: list[dict[str, float]], dust_xrp: float = 0.01) -> list[dict[str, float]]:
    if not levels:
        return []

    non_dust = [row for row in levels if row["xrp_value"] >= dust_xrp and row["price"] > 0]
    if not non_dust:
        return []

    prices = [row["price"] for row in non_dust]
    med = median(prices)
    # Reject extreme price outliers above/below 5x median.
    return [row for row in non_dust if med / 5 <= row["price"] <= med * 5]


def derive_price_from_orderbook(parsed: dict[str, object]) -> float | None:
    best_bid = parsed.get("best_bid")
    best_ask = parsed.get("best_ask")

    if best_bid and best_ask:
        return (float(best_bid["price"]) + float(best_ask["price"])) / 2.0
    if best_ask:
        return float(best_ask["price"])
    if best_bid:
        return float(best_bid["price"])
    return None


def calculate_spread(parsed: dict[str, object]) -> float | None:
    best_bid = parsed.get("best_bid")
    best_ask = parsed.get("best_ask")
    if not best_bid or not best_ask:
        return None
    ask = float(best_ask["price"])
    bid = float(best_bid["price"])
    if ask <= 0:
        return None
    return ((ask - bid) / ask) * 100.0


def calculate_liquidity(parsed: dict[str, object], depth_levels: int = 8) -> float:
    bids = _filtered_levels(list(parsed.get("bids", [])))[:depth_levels]
    asks = _filtered_levels(list(parsed.get("asks", [])))[:depth_levels]
    return sum(row["xrp_value"] for row in bids) + sum(row["xrp_value"] for row in asks)


def calculate_autobridge_price() -> None:
    # Placeholder for future token -> XRP -> token routed pricing.
    return None


def build_snapshot_from_offers(offers: list[dict[str, float]]) -> dict[str, object]:
    parsed = parse_orderbook(offers)
    price = derive_price_from_orderbook(parsed)
    spread = calculate_spread(parsed)
    liquidity = calculate_liquidity(parsed)

    return {
        "parsed": parsed,
        "price_xrp": price,
        "spread_pct": spread,
        "liquidity_xrp": liquidity,
        "bid_count": len(parsed["bids"]),
        "ask_count": len(parsed["asks"]),
        "order_count": len(parsed["bids"]) + len(parsed["asks"]),
    }
