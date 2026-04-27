from __future__ import annotations

from app.strategies.base import StrategyContext


def build_scanner_context(
    issuer: str,
    currency: str,
    price_xrp: float | None,
    spread_pct: float | None,
    liquidity_xrp: float,
    bid_count: int,
    ask_count: int,
) -> StrategyContext:
    return StrategyContext(
        issuer=issuer,
        currency=currency,
        current_price_xrp=price_xrp,
        spread_pct=spread_pct,
        liquidity_xrp=liquidity_xrp,
        bid_count=bid_count,
        ask_count=ask_count,
    )
