from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .models import Signal, TradeDecision


@dataclass(slots=True)
class MeanReversionStrategy:
    symbol: str
    lookback: int = 20
    z_buy: float = -1.0
    z_sell: float = 1.0
    _prices: deque[float] = field(default_factory=deque)

    def update(self, price: float) -> TradeDecision:
        self._prices.append(price)
        if len(self._prices) > self.lookback:
            self._prices.popleft()

        if len(self._prices) < self.lookback:
            return TradeDecision(self.symbol, Signal.HOLD, 0.0, "warming up")

        mean = sum(self._prices) / len(self._prices)
        variance = sum((p - mean) ** 2 for p in self._prices) / len(self._prices)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return TradeDecision(self.symbol, Signal.HOLD, 0.0, "zero variance")

        z_score = (price - mean) / std_dev

        if z_score <= self.z_buy:
            confidence = min(1.0, abs(z_score) / abs(self.z_buy))
            return TradeDecision(self.symbol, Signal.BUY, confidence, f"z={z_score:.2f}")

        if z_score >= self.z_sell:
            confidence = min(1.0, abs(z_score) / abs(self.z_sell))
            return TradeDecision(self.symbol, Signal.SELL, confidence, f"z={z_score:.2f}")

        return TradeDecision(self.symbol, Signal.HOLD, max(0.0, 1.0 - abs(z_score)), f"z={z_score:.2f}")
