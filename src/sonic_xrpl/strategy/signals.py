"""Signal models for the strategy layer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    NEUTRAL = "neutral"


@dataclass
class Signal:
    """A trading signal produced by a strategy.

    Signals are informational only. They are consumed by the Risk layer
    which decides whether to create an ExecutionIntent.
    """

    signal_type: SignalType
    asset: str
    confidence: float
    notes: str = ""
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Signal.confidence must be in [0, 1], got {self.confidence}"
            )
