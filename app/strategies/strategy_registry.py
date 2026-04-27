"""Strategy registry — maps names to strategy instances."""

from __future__ import annotations

from app.strategies.base import BaseStrategy
from app.strategies.new_token_scanner import NewTokenScannerStrategy

_REGISTRY: dict[str, BaseStrategy] = {}


def _build_default_registry() -> dict[str, BaseStrategy]:
    strategies: list[BaseStrategy] = [
        NewTokenScannerStrategy(),
    ]
    return {s.name: s for s in strategies}


def get_registry() -> dict[str, BaseStrategy]:
    """Return the shared strategy registry (initialised on first call)."""
    global _REGISTRY
    if not _REGISTRY:
        _REGISTRY = _build_default_registry()
    return _REGISTRY


def get_strategy(name: str) -> BaseStrategy:
    reg = get_registry()
    if name not in reg:
        raise KeyError(f"Strategy {name!r} not found. Available: {list(reg)}")
    return reg[name]
