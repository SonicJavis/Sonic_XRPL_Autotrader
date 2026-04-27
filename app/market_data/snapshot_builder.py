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


def calculate_best_price(parsed: dict[str, object]) -> dict[str, float | None]:
    direct_price = derive_price_from_orderbook(parsed)
    autobridge_price = None
    return {
        "direct_price": direct_price,
        "autobridge_price": autobridge_price,
        "best_price": direct_price,
    }


def calculate_spread(parsed: dict[str, object]) -> float | None:
    best_bid = parsed.get("best_bid")
    best_ask = parsed.get("best_ask")
    if not best_bid or not best_ask:
        return None
    ask = float(best_ask["price"])
    bid = float(best_bid["price"])
    if ask <= 0:
        return None
    spread = ((ask - bid) / ask) * 100.0
    if spread < 0:
        return None
    return spread


def calculate_liquidity(parsed: dict[str, object], depth_levels: int = 8) -> dict[str, float | bool]:
    bids = _filtered_levels(list(parsed.get("bids", [])))[:depth_levels]
    asks = _filtered_levels(list(parsed.get("asks", [])))[:depth_levels]

    liquidity_bid = sum(row["xrp_value"] for row in bids)
    liquidity_ask = sum(row["xrp_value"] for row in asks)
    total = liquidity_bid + liquidity_ask

    dominated = False
    if total > 0:
        bid_share = liquidity_bid / total
        ask_share = liquidity_ask / total
        dominated = bid_share > 0.9 or ask_share > 0.9

    return {
        "liquidity_bid_xrp": liquidity_bid,
        "liquidity_ask_xrp": liquidity_ask,
        "total_liquidity_xrp": total,
        "one_sided_dominance": dominated,
    }


def calculate_autobridge_price() -> None:
    # Placeholder for future token -> XRP -> token routed pricing.
    return None


def build_snapshot_from_offers(offers: list[dict[str, float]]) -> dict[str, object]:
    parsed = parse_orderbook(offers)
    best_price = calculate_best_price(parsed)
    price = best_price["best_price"]
    spread = calculate_spread(parsed)
    liquidity = calculate_liquidity(parsed)

    valid = True
    invalid_reasons: list[str] = []

    if price is None:
        valid = False
        invalid_reasons.append("missing_price")
    if spread is None:
        valid = False
        invalid_reasons.append("invalid_or_missing_spread")
    if liquidity["total_liquidity_xrp"] <= 0:
        valid = False
        invalid_reasons.append("zero_liquidity")
    if parsed["best_bid"] is None or parsed["best_ask"] is None:
        valid = False
        invalid_reasons.append("one_sided_book")

    return {
        "parsed": parsed,
        "price_xrp": price,
        "spread_pct": spread,
        "liquidity_bid_xrp": liquidity["liquidity_bid_xrp"],
        "liquidity_ask_xrp": liquidity["liquidity_ask_xrp"],
        "liquidity_xrp": liquidity["total_liquidity_xrp"],
        "one_sided_dominance": liquidity["one_sided_dominance"],
        "bid_count": len(parsed["bids"]),
        "ask_count": len(parsed["asks"]),
        "order_count": len(parsed["bids"]) + len(parsed["asks"]),
        "raw_offer_count": parsed["raw_offer_count"],
        "filtered_offer_count": parsed["filtered_offer_count"],
        "rejected_orders": parsed["rejected_orders"],
        "price_deviation_warnings": parsed["price_deviation_warnings"],
        "valid": valid,
        "invalid_reasons": invalid_reasons,
        "best_price": best_price,
    }
