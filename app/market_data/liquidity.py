from __future__ import annotations

from typing import Any


def estimate_liquidity_xrp(book_offers_result: dict[str, Any]) -> float:
    offers = book_offers_result.get("offers", [])
    return float(len(offers)) * 100.0
