from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Signal(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(slots=True)
class MarketTick:
    symbol: str
    price: float
    timestamp_iso: str


@dataclass(slots=True)
class TradeDecision:
    symbol: str
    signal: Signal
    confidence: float
    reason: str
