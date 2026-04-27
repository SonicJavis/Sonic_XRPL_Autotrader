from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MarketMetrics:
    price_xrp: float | None
    liquidity_xrp: float
    spread_pct: float | None
    volume_estimate: float
    tx_count: int
    bid_count: int = 0
    ask_count: int = 0
