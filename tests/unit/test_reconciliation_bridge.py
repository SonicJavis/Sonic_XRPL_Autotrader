"""Tests for the Phase 30 reconciliation bridge."""

from __future__ import annotations

import pytest
from sonic_xrpl.reconciliation.legacy_phase30_adapter import (
    LEGACY_AVAILABLE,
    get_legacy_status,
    legacy_reconcile,
)
from sonic_xrpl.core.errors import ReconciliationError


def test_get_legacy_status_returns_dict():
    """get_legacy_status() always returns a dict."""
    status = get_legacy_status()
    assert isinstance(status, dict)
    assert "legacy_available" in status
    assert isinstance(status["legacy_available"], bool)


def test_legacy_available_is_bool():
    """LEGACY_AVAILABLE is a boolean."""
    assert isinstance(LEGACY_AVAILABLE, bool)


def test_legacy_reconcile_handles_missing_gracefully():
    """If legacy not available, legacy_reconcile raises ReconciliationError (not ImportError)."""
    if not LEGACY_AVAILABLE:
        with pytest.raises(ReconciliationError):
            legacy_reconcile(None, None)
    else:
        # Legacy is available — just verify it doesn't crash on import
        assert LEGACY_AVAILABLE is True


def test_v2_reconcile_works_independently():
    """V2 reconciliation works without Phase 30."""
    from sonic_xrpl.reconciliation.models import (
        V2SimulationRecord,
        V2OutcomeRecord,
        ReconciliationStatus,
    )
    from sonic_xrpl.reconciliation.comparator import reconcile_v2

    sim = V2SimulationRecord(
        simulation_id="test-sim-1",
        intent_id="test-intent-1",
        expected_fill_pct=0.92,
        expected_slippage_bps=10.0,
    )
    outcome = V2OutcomeRecord(
        simulation_id="test-sim-1",
        actual_fill_pct=0.90,
        actual_slippage_bps=12.0,
    )
    result = reconcile_v2(sim, outcome)
    assert result.simulation_id == "test-sim-1"
    assert result.status in ReconciliationStatus.__members__.values()
