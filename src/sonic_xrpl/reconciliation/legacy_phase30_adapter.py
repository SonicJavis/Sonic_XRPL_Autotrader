"""Legacy Phase 30 Adapter.

Detects whether execution_prototype.reconciliation (Phase 30) is available
and exposes a V2-compatible interface.

Architecture Rule #12: Reconciliation must preserve Phase 30 compatibility.

If legacy Phase 30 is present:
  LEGACY_AVAILABLE = True
  Phase 30 functions are proxied through V2 interface.

If legacy Phase 30 is absent:
  LEGACY_AVAILABLE = False
  Stub functions are provided that raise ReconciliationError with clear message.
"""

from __future__ import annotations

from sonic_xrpl.core.errors import ReconciliationError

# Attempt to import Phase 30 modules
try:
    from execution_prototype.reconciliation.models import (
        SimulationRecord as _LegacySimulationRecord,
        LifecycleRecord as _LegacyLifecycleRecord,
        ReconciliationRecord as _LegacyReconciliationRecord,
    )
    from execution_prototype.reconciliation.comparator import (
        reconcile as _legacy_reconcile,
        generate_reconciliation_id as _legacy_generate_id,
    )
    LEGACY_AVAILABLE = True
    _LEGACY_IMPORT_ERROR: str | None = None
except ImportError as exc:
    LEGACY_AVAILABLE = False
    _LEGACY_IMPORT_ERROR = str(exc)
    _LegacySimulationRecord = None  # type: ignore[assignment, misc]
    _LegacyLifecycleRecord = None  # type: ignore[assignment, misc]
    _LegacyReconciliationRecord = None  # type: ignore[assignment, misc]
    _legacy_reconcile = None  # type: ignore[assignment]
    _legacy_generate_id = None  # type: ignore[assignment]


def get_legacy_status() -> dict:
    """Return the availability status of the legacy Phase 30 module."""
    return {
        "legacy_available": LEGACY_AVAILABLE,
        "import_error": _LEGACY_IMPORT_ERROR,
        "module": "execution_prototype.reconciliation",
    }


def legacy_reconcile(sim_record, lifecycle_record):
    """Proxy to Phase 30 reconcile() if available.

    Raises ReconciliationError if legacy module is not available.
    """
    if not LEGACY_AVAILABLE:
        raise ReconciliationError(
            f"Phase 30 reconciliation module is not available: {_LEGACY_IMPORT_ERROR}. "
            "Use V2 reconciliation from sonic_xrpl.reconciliation.comparator instead."
        )
    return _legacy_reconcile(sim_record, lifecycle_record)


def legacy_generate_id(*args) -> str:
    """Proxy to Phase 30 generate_reconciliation_id() if available."""
    if not LEGACY_AVAILABLE:
        raise ReconciliationError(
            "Phase 30 reconciliation module is not available."
        )
    return _legacy_generate_id(*args)


def legacy_simulation_record_class():
    """Return the Phase 30 SimulationRecord class if available."""
    if not LEGACY_AVAILABLE:
        raise ReconciliationError(
            "Phase 30 reconciliation module is not available."
        )
    return _LegacySimulationRecord


def legacy_lifecycle_record_class():
    """Return the Phase 30 LifecycleRecord class if available."""
    if not LEGACY_AVAILABLE:
        raise ReconciliationError(
            "Phase 30 reconciliation module is not available."
        )
    return _LegacyLifecycleRecord
