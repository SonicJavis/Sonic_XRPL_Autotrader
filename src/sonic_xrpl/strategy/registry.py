"""Strategy registry — maps strategy IDs to instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sonic_xrpl.strategy.base import BaseStrategy


class StrategyRegistry:
    """Maintains a collection of registered strategies."""

    def __init__(self) -> None:
        self._strategies: dict[str, "BaseStrategy"] = {}

    def register(self, strategy: "BaseStrategy") -> None:
        """Register a strategy by its strategy_id."""
        self._strategies[strategy.strategy_id] = strategy

    def get(self, strategy_id: str) -> "BaseStrategy":
        """Return a strategy by ID. Raises KeyError if not found."""
        if strategy_id not in self._strategies:
            raise KeyError(f"Unknown strategy: {strategy_id!r}")
        return self._strategies[strategy_id]

    def list_all(self) -> list[str]:
        """Return all registered strategy IDs."""
        return sorted(self._strategies.keys())

    def __len__(self) -> int:
        return len(self._strategies)


# Module-level global registry
_global_registry = StrategyRegistry()


def get_global_registry() -> StrategyRegistry:
    """Return the module-level global strategy registry."""
    return _global_registry
