"""DB-backed runtime state models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KillSwitchState:
    """Persistent kill switch state."""

    is_active: bool
    updated_at: str
    reason: str
    updated_by: str
