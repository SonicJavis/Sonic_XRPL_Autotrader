"""Tests for the Live Guard — all submission must be blocked."""

from __future__ import annotations

import pytest
from sonic_xrpl.core.errors import LiveTradingDisabledError, ModeViolationError
from sonic_xrpl.core.modes import RuntimeMode
from sonic_xrpl.execution.live_guard import (
    assert_live_disabled,
    assert_can_create_intent,
    assert_can_simulate,
    assert_can_paper_trade,
    assert_can_submit,
    block_signing,
    block_autofill,
    block_wallet_construction,
)


def test_assert_live_disabled_always_raises():
    """assert_live_disabled() always raises LiveTradingDisabledError."""
    with pytest.raises(LiveTradingDisabledError):
        assert_live_disabled()


@pytest.mark.parametrize("mode", list(RuntimeMode))
def test_assert_can_submit_always_raises(mode):
    """assert_can_submit() raises for ALL modes in Phase 45."""
    with pytest.raises(LiveTradingDisabledError):
        assert_can_submit(mode)


def test_assert_can_create_intent_simulation_ok():
    """SIMULATION mode can create intent."""
    assert_can_create_intent(RuntimeMode.SIMULATION)  # Must not raise


def test_assert_can_create_intent_paper_ok():
    """PAPER mode can create intent."""
    assert_can_create_intent(RuntimeMode.PAPER)  # Must not raise


def test_assert_can_create_intent_intelligence_raises():
    """INTELLIGENCE_ONLY mode cannot create intent."""
    with pytest.raises(ModeViolationError):
        assert_can_create_intent(RuntimeMode.INTELLIGENCE_ONLY)


def test_assert_can_simulate_simulation_ok():
    """SIMULATION mode can simulate."""
    assert_can_simulate(RuntimeMode.SIMULATION)  # Must not raise


def test_assert_can_simulate_paper_raises():
    """PAPER mode cannot simulate."""
    with pytest.raises(ModeViolationError):
        assert_can_simulate(RuntimeMode.PAPER)


def test_assert_can_paper_trade_paper_ok():
    """PAPER mode can paper trade."""
    assert_can_paper_trade(RuntimeMode.PAPER)  # Must not raise


def test_assert_can_paper_trade_simulation_raises():
    """SIMULATION mode cannot paper trade."""
    with pytest.raises(ModeViolationError):
        assert_can_paper_trade(RuntimeMode.SIMULATION)


def test_block_signing_raises():
    """block_signing() raises LiveTradingDisabledError."""
    with pytest.raises(LiveTradingDisabledError):
        block_signing()


def test_block_autofill_raises():
    """block_autofill() raises LiveTradingDisabledError."""
    with pytest.raises(LiveTradingDisabledError):
        block_autofill()


def test_block_wallet_construction_raises():
    """block_wallet_construction() raises LiveTradingDisabledError."""
    with pytest.raises(LiveTradingDisabledError):
        block_wallet_construction()
