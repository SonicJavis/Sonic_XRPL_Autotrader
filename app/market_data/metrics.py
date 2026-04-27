from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MarketMetrics:
    price_xrp: float
    liquidity_xrp: float
    spread_pct: float
    volume_estimate: float
    tx_count: int
