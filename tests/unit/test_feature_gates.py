"""Tests for feature gates."""

from __future__ import annotations

import pytest
from sonic_xrpl.core.errors import CapabilityNotAvailableError
from sonic_xrpl.protocol.feature_gates import (
    is_feature_enabled,
    require_feature,
    is_research_only,
    is_obsolete,
)


def test_amm_is_enabled():
    """AMM should be enabled on mainnet."""
    assert is_feature_enabled("AMM") is True


def test_clawback_is_enabled():
    """Clawback should be enabled."""
    assert is_feature_enabled("Clawback") is True


def test_lending_is_not_enabled():
    """LendingProtocol should NOT be enabled (feature-gated)."""
    assert is_feature_enabled("LendingProtocol") is False


def test_require_feature_amm_passes():
    """require_feature("AMM") should not raise."""
    require_feature("AMM")  # Should not raise


def test_require_feature_lending_raises():
    """require_feature("LendingProtocol") should raise CapabilityNotAvailableError."""
    with pytest.raises(CapabilityNotAvailableError):
        require_feature("LendingProtocol")


def test_require_feature_unknown_raises():
    """require_feature on an unknown feature raises CapabilityNotAvailableError."""
    with pytest.raises(CapabilityNotAvailableError):
        require_feature("NonExistentFeature123")


def test_hooks_are_research_only():
    """Hooks on XRPL mainnet is research-only."""
    assert is_research_only("HooksOnMainnet") is True


def test_batch_is_obsolete():
    """Batch amendment is obsolete."""
    assert is_obsolete("Batch") is True


def test_amm_is_not_obsolete():
    """AMM is not obsolete."""
    assert is_obsolete("AMM") is False
