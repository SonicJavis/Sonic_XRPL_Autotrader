"""Strategy base — abstract signal generator.

Strategy does NOT execute (Architecture Rule #7).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sonic_xrpl.strategy.signals import Signal


class BaseStrategy(ABC):
    """Abstract base for all V2 strategies.

    Strategies generate Signals. They do not execute trades.
    Execution is handled downstream by the Risk -> Execution pipeline.
    """

    strategy_id: str
    name: str

    @abstractmethod
    def generate_signals(self, data: Any) -> list[Signal]:
        """Generate trading signals from market data.

        Args:
            data: Market data snapshot (type depends on strategy).

        Returns:
            List of Signal objects. May be empty.
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.strategy_id!r}, name={self.name!r})"
