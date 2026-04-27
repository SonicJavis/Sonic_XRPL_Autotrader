from __future__ import annotations

from app.strategies.base import BaseStrategy, SignalCandidate, StrategyContext


class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, BaseStrategy] = {}

    def register(self, strategy: BaseStrategy) -> None:
        self._strategies[strategy.name] = strategy

    def list_strategies(self) -> list[str]:
        return sorted(self._strategies.keys())

    def run_all_strategies(self, context: StrategyContext) -> list[SignalCandidate]:
        results: list[SignalCandidate] = []
        for strategy in self._strategies.values():
            candidate = strategy.generate_signal(context)
            if candidate is not None:
                results.append(candidate)
        return results
