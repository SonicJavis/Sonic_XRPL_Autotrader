"""Tests for execution intent and plan models."""

from __future__ import annotations

import pytest
from sonic_xrpl.core.modes import RuntimeMode
from sonic_xrpl.execution.intent import ExecutionIntent, IntentStatus
from sonic_xrpl.execution.plan import ExecutionPlan


def test_execution_intent_creation():
    """ExecutionIntent can be created with required fields."""
    intent = ExecutionIntent(
        mode=RuntimeMode.SIMULATION,
        strategy_id="test-strategy",
        asset_in="XRP",
        asset_out="USD",
        amount=100.0,
    )
    assert intent.intent_id  # auto-generated
    assert intent.status == IntentStatus.PENDING
    assert intent.mode == RuntimeMode.SIMULATION


def test_execution_intent_invalid_amount():
    """ExecutionIntent raises ValueError for non-positive amount."""
    with pytest.raises(ValueError):
        ExecutionIntent(
            mode=RuntimeMode.SIMULATION,
            strategy_id="s",
            asset_in="XRP",
            asset_out="USD",
            amount=0,
        )


def test_execution_intent_invalid_confidence():
    """ExecutionIntent raises ValueError for confidence outside [0, 1]."""
    with pytest.raises(ValueError):
        ExecutionIntent(
            mode=RuntimeMode.SIMULATION,
            strategy_id="s",
            asset_in="XRP",
            asset_out="USD",
            amount=1.0,
            confidence=1.5,
        )


def test_execution_plan_live_submission_always_false():
    """ExecutionPlan.live_submission_allowed is always False."""
    plan = ExecutionPlan(intent_id="test-intent-id")
    assert plan.live_submission_allowed is False


def test_execution_plan_cannot_enable_submission():
    """Setting live_submission_allowed=True is overridden to False."""
    plan = ExecutionPlan(intent_id="test-intent-id")
    # live_submission_allowed should be False regardless
    assert plan.live_submission_allowed is False
