from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class StrategyContext:
    issuer: str
    currency: str
    current_price_xrp: float | None
    spread_pct: float | None
    liquidity_xrp: float
    bid_count: int
    ask_count: int


@dataclass(slots=True)
class SignalCandidate:
    strategy_name: str
    issuer: str
    currency: str
    side: str
    confidence: float
    risk_score: float
    suggested_size_xrp: float
    reason: str
    invalidation_condition: str


class BaseStrategy(ABC):
    name: str

    @abstractmethod
    def generate_signal(self, context: StrategyContext) -> SignalCandidate | None:
        raise NotImplementedError
