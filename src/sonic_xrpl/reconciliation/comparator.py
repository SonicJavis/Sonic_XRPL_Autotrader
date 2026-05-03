"""V2 Reconciliation comparator.

Compares simulation vs outcome records and produces reconciliation results.
"""

from __future__ import annotations

from sonic_xrpl.reconciliation.models import (
    ReconciliationStatus,
    V2OutcomeRecord,
    V2ReconciliationRecord,
    V2SimulationRecord,
)


def reconcile_v2(
    sim: V2SimulationRecord,
    outcome: V2OutcomeRecord,
) -> V2ReconciliationRecord:
    """Compare a simulation record against an observed outcome.

    Returns a V2ReconciliationRecord with drift flags where applicable.
    """
    flags: list[str] = []
    fill_delta: float | None = None
    slippage_delta: float | None = None

    # Fill comparison
    if sim.expected_fill_pct is not None and outcome.actual_fill_pct is not None:
        fill_delta = outcome.actual_fill_pct - sim.expected_fill_pct
        if abs(fill_delta) > 0.05:
            flags.append("FILL_DRIFT")
    elif sim.expected_fill_pct is not None and outcome.actual_fill_pct is None:
        flags.append("MISSING_ACTUAL_FILL")

    # Slippage comparison
    if (
        sim.expected_slippage_bps is not None
        and outcome.actual_slippage_bps is not None
    ):
        slippage_delta = outcome.actual_slippage_bps - sim.expected_slippage_bps
        if abs(slippage_delta) > 20:
            flags.append("SLIPPAGE_DRIFT")
    elif sim.expected_slippage_bps is not None and outcome.actual_slippage_bps is None:
        flags.append("MISSING_ACTUAL_SLIPPAGE")

    status = ReconciliationStatus.DRIFT_DETECTED if flags else ReconciliationStatus.MATCHED

    return V2ReconciliationRecord(
        simulation_id=sim.simulation_id,
        status=status,
        fill_delta=fill_delta,
        slippage_delta=slippage_delta,
        drift_flags=flags,
    )
