from __future__ import annotations

from app.strategies.base import StrategyContext


def build_scanner_context(price_xrp: float = 1.0) -> StrategyContext:
    return StrategyContext(current_price_xrp=price_xrp)
