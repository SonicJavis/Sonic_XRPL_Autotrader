"""Tests for the Protocol Capability Matrix."""

from __future__ import annotations

import pytest
from sonic_xrpl.protocol.amendments import AmendmentStatus
from sonic_xrpl.protocol.capability_matrix import (
    CAPABILITY_MATRIX,
    get_capability,
    get_enabled_capabilities,
    get_obsolete_capabilities,
    get_research_only_capabilities,
    is_capability_available,
    require_capability,
)
from sonic_xrpl.core.errors import CapabilityNotAvailableError


def test_capability_matrix_not_empty():
    """Capability matrix must have entries."""
    assert len(CAPABILITY_MATRIX) > 5


def test_amm_is_available():
    """AMM must be available."""
    assert is_capability_available("AMM") is True


def test_lending_not_available():
    """LendingProtocol must not be available."""
    assert is_capability_available("LendingProtocol") is False


def test_obsolete_not_in_enabled():
    """No obsolete amendment should be in the enabled list."""
    enabled = set(get_enabled_capabilities())
    obsolete = set(get_obsolete_capabilities())
    overlap = enabled & obsolete
    assert not overlap, f"Obsolete amendments in enabled list: {overlap}"


def test_research_only_not_in_enabled():
    """No research-only amendment should be in the enabled list."""
    enabled = set(get_enabled_capabilities())
    research = set(get_research_only_capabilities())
    overlap = enabled & research
    assert not overlap, f"Research-only capabilities in enabled list: {overlap}"


def test_known_enabled_capabilities():
    """Specific expected-enabled capabilities are present."""
    expected_enabled = [
        "AMM", "AMMClawback", "Clawback", "Credentials", "DID",
        "DeepFreeze", "ExpandedSignerList", "MPTokensV1", "PriceOracle",
    ]
    enabled = get_enabled_capabilities()
    for cap in expected_enabled:
        assert cap in enabled, f"Expected {cap} to be enabled"


def test_get_capability_unknown_raises():
    """get_capability raises KeyError for unknown capability."""
    with pytest.raises(KeyError):
        get_capability("ImaginaryCapability999")


def test_require_capability_raises_when_not_enabled():
    """require_capability raises CapabilityNotAvailableError for feature-gated."""
    with pytest.raises(CapabilityNotAvailableError):
        require_capability("LendingProtocol")


def test_capability_entry_has_required_fields():
    """Each capability entry has required fields."""
    for name, cap in CAPABILITY_MATRIX.items():
        assert cap.name == name
        assert cap.source
        assert cap.architecture_impact
        assert cap.last_checked
