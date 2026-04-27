"""Tests for strategy signal generation."""

from __future__ import annotations

from app.strategies.base import SignalPayload
from app.strategies.new_token_scanner import NewTokenScannerStrategy
from app.strategies.strategy_registry import get_registry, get_strategy


def test_new_token_scanner_name():
    s = NewTokenScannerStrategy()
    assert s.name == "new_token_scanner"


def test_new_token_scanner_signal_or_none():
    s = NewTokenScannerStrategy()
    # Run several ticks — at least one should produce a signal eventually.
    signals = [s.generate_signal() for _ in range(20)]
    non_none = [sig for sig in signals if sig is not None]
    assert len(non_none) > 0, "Expected at least one signal in 20 ticks"
    for sig in non_none:
        assert isinstance(sig, SignalPayload)
        assert sig.direction == "BUY"
        assert sig.price_xrp > 0


def test_registry_contains_scanner():
    reg = get_registry()
    assert "new_token_scanner" in reg


def test_get_strategy():
    s = get_strategy("new_token_scanner")
    assert s.name == "new_token_scanner"


def test_get_strategy_missing():
    try:
        get_strategy("nonexistent")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass
