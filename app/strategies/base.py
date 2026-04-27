"""Base strategy interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SignalPayload:
    """Carries all information from a strategy signal to the execution layer."""

    strategy_name: str
    currency: str
    issuer: str
    direction: str  # "BUY" | "SELL"
    price_xrp: float
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseStrategy(ABC):
    """All trading strategies must inherit from this class."""

    name: str = "base"

    @abstractmethod
    def generate_signal(self) -> SignalPayload | None:
        """Produce a signal or return None if no opportunity is detected."""
        ...

    def __repr__(self) -> str:
        return f"<Strategy name={self.name!r}>"
