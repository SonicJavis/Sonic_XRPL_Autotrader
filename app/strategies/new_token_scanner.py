from __future__ import annotations

from app.config import Settings
from app.strategies.base import BaseStrategy, SignalCandidate, StrategyContext


class NewTokenScannerStrategy(BaseStrategy):
    name = "new_token_scanner"

    def __init__(self, settings: Settings, min_confidence: float = 0.6) -> None:
        self.settings = settings
        self.min_confidence = min_confidence

    def generate_signal(self, context: StrategyContext) -> SignalCandidate | None:
        if context.bid_count == 0 or context.ask_count == 0:
            return SignalCandidate(
                strategy_name=self.name,
                issuer=context.issuer,
                currency=context.currency,
                side="HOLD",
                confidence=0.0,
                risk_score=1.0,
                suggested_size_xrp=0.0,
                reason="missing bid/ask side",
                invalidation_condition="book remains one-sided",
            )

        if context.spread_pct is None or context.spread_pct > self.settings.MAX_SPREAD_PCT:
            return SignalCandidate(
                strategy_name=self.name,
                issuer=context.issuer,
                currency=context.currency,
                side="HOLD",
                confidence=0.0,
                risk_score=0.9,
                suggested_size_xrp=0.0,
                reason="spread too wide",
                invalidation_condition="spread tightens below threshold",
            )

        if context.liquidity_xrp < self.settings.MIN_LIQUIDITY_XRP:
            return SignalCandidate(
                strategy_name=self.name,
                issuer=context.issuer,
                currency=context.currency,
                side="HOLD",
                confidence=0.0,
                risk_score=0.9,
                suggested_size_xrp=0.0,
                reason="insufficient liquidity",
                invalidation_condition="liquidity improves",
            )

        if (context.bid_count + context.ask_count) <= 2:
            return SignalCandidate(
                strategy_name=self.name,
                issuer=context.issuer,
                currency=context.currency,
                side="HOLD",
                confidence=0.0,
                risk_score=0.95,
                suggested_size_xrp=0.0,
                reason="thin orderbook",
                invalidation_condition="book depth increases",
            )

        confidence = 0.55
        if context.spread_pct <= max(0.2, self.settings.MAX_SPREAD_PCT / 4):
            confidence += 0.15
        imbalance = abs(context.bid_count - context.ask_count)
        if imbalance <= 1:
            confidence += 0.1
        if context.liquidity_xrp >= self.settings.MIN_LIQUIDITY_XRP * 2:
            confidence += 0.1
        if context.current_price_xrp and context.current_price_xrp > 0:
            confidence += 0.05

        confidence = min(1.0, confidence)
        if confidence < self.min_confidence:
            return SignalCandidate(
                strategy_name=self.name,
                issuer=context.issuer,
                currency=context.currency,
                side="HOLD",
                confidence=confidence,
                risk_score=0.1,
                suggested_size_xrp=0.0,
                reason="confidence below threshold",
                invalidation_condition="confidence remains low",
            )

        return SignalCandidate(
            strategy_name=self.name,
            issuer=context.issuer,
            currency=context.currency,
            side="BUY",
            confidence=confidence,
            risk_score=0.2,
            suggested_size_xrp=min(self.settings.MAX_TRADE_XRP, max(1.0, context.liquidity_xrp / 5000.0)),
            reason="book structure and liquidity pass scanner checks",
            invalidation_condition="liquidity falls below threshold",
        )
