from __future__ import annotations

from typing import Any


def estimate_spread_pct(book_offers_result: dict[str, Any]) -> float:
    offers = book_offers_result.get("offers", [])
    if len(offers) < 2:
        return 0.0
    return 0.5
