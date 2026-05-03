"""V2 Reconciliation models.

Architecture Rule #12: Reconciliation must preserve Phase 30 compatibility.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReconciliationStatus(str, Enum):
    MATCHED = "matched"
    DRIFT_DETECTED = "drift_detected"
    MISSING_DATA = "missing_data"
    AMBIGUOUS = "ambiguous"


@dataclass
class V2SimulationRecord:
    """V2 version of a simulation record for reconciliation."""

    simulation_id: str
    intent_id: str
    expected_fill_pct: float | None = None
    expected_slippage_bps: float | None = None
    expected_fee_drops: int | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class V2OutcomeRecord:
    """V2 version of an observed outcome record for reconciliation."""

    simulation_id: str
    actual_fill_pct: float | None = None
    actual_slippage_bps: float | None = None
    actual_fee_drops: int | None = None
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class V2ReconciliationRecord:
    """A reconciliation result comparing simulation vs outcome."""

    simulation_id: str
    status: ReconciliationStatus
    fill_delta: float | None = None
    slippage_delta: float | None = None
    drift_flags: list[str] = field(default_factory=list)
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reconciled_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
