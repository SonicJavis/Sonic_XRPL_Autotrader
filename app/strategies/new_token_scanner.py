from __future__ import annotations

from app.market_data.token_registry import TokenRegistry
from app.strategies.base import BaseStrategy, SignalCandidate, StrategyContext


class NewTokenScannerStrategy(BaseStrategy):
    name = "new_token_scanner"

    def __init__(self, token_registry: TokenRegistry, min_confidence: float = 0.6) -> None:
        self.token_registry = token_registry
        self.min_confidence = min_confidence

    def generate_signal(self, context: StrategyContext) -> SignalCandidate | None:
        tokens = self.token_registry.list_tokens()
        if not tokens:
            return None

        token = tokens[0]
        confidence = 0.75 if context.current_price_xrp > 0 else 0.0
        if confidence < self.min_confidence:
            return SignalCandidate(
                strategy_name=self.name,
                issuer=token.issuer,
                currency=token.currency,
                side="HOLD",
                confidence=confidence,
                risk_score=0.1,
                suggested_size_xrp=0.0,
                reason="confidence below threshold",
                invalidation_condition="confidence remains low",
            )

        return SignalCandidate(
            strategy_name=self.name,
            issuer=token.issuer,
            currency=token.currency,
            side="BUY",
            confidence=confidence,
            risk_score=0.2,
            suggested_size_xrp=1.0,
            reason="new token candidate passes scanner confidence",
            invalidation_condition="liquidity falls below threshold",
        )
