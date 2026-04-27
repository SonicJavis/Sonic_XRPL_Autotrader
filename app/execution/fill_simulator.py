from __future__ import annotations


def simulate_fill(asks: list[dict[str, float]], target_size_xrp: float) -> dict[str, float | bool]:
    """Deterministic orderbook walk for paper execution realism."""
    if target_size_xrp <= 0:
        return {
            "filled_size_xrp": 0.0,
            "avg_price": 0.0,
            "slippage_pct": 0.0,
            "fill_success": True,
            "partial_fill": False,
        }

    best_ask = 0.0
    for level in asks:
        p = float(level.get("price", 0.0))
        if p > 0:
            best_ask = p
            break

    if not asks or best_ask <= 0:
        return {
            "filled_size_xrp": 0.0,
            "avg_price": 0.0,
            "slippage_pct": 100.0,
            "fill_success": False,
            "partial_fill": False,
        }

    remaining_xrp = float(target_size_xrp)
    spent_xrp = 0.0
    tokens_bought = 0.0

    for level in asks:
        price = float(level.get("price", 0.0))
        xrp_value = float(level.get("xrp_value", 0.0))
        token_amount = float(level.get("token_amount", 0.0))
        if price <= 0 or xrp_value <= 0 or token_amount <= 0:
            continue

        take_xrp = min(remaining_xrp, xrp_value)
        token_take = (take_xrp / xrp_value) * token_amount
        spent_xrp += take_xrp
        tokens_bought += token_take
        remaining_xrp -= take_xrp

        if remaining_xrp <= 0:
            break

    if spent_xrp <= 0 or tokens_bought <= 0:
        return {
            "filled_size_xrp": 0.0,
            "avg_price": 0.0,
            "slippage_pct": 100.0,
            "fill_success": False,
            "partial_fill": False,
        }

    avg_price = spent_xrp / tokens_bought
    slippage_pct = max(0.0, ((avg_price - best_ask) / best_ask) * 100.0)
    partial_fill = remaining_xrp > 1e-9

    return {
        "filled_size_xrp": spent_xrp,
        "avg_price": avg_price,
        "slippage_pct": slippage_pct,
        "fill_success": not partial_fill,
        "partial_fill": partial_fill,
    }
