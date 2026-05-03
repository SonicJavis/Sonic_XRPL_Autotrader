"""Runtime modes for Sonic XRPL V2.

Default mode: INTELLIGENCE_ONLY.
Live trading: BLOCKED in Phase 45.
"""

from __future__ import annotations

import os
from enum import Enum


class RuntimeMode(str, Enum):
    """Strict runtime modes controlling what operations are permitted."""

    INTELLIGENCE_ONLY = "intelligence_only"
    RESEARCH = "research"
    SIMULATION = "simulation"
    PAPER = "paper"
    LIVE_READINESS = "live_readiness"
    LIVE = "live"


DEFAULT_MODE = RuntimeMode.INTELLIGENCE_ONLY


def get_current_mode() -> RuntimeMode:
    """Return the current runtime mode from environment, defaulting to INTELLIGENCE_ONLY."""
    raw = os.environ.get("SONIC_RUNTIME_MODE", RuntimeMode.INTELLIGENCE_ONLY.value)
    try:
        return RuntimeMode(raw.lower())
    except ValueError:
        return RuntimeMode.INTELLIGENCE_ONLY


class ModeContext:
    """Holds the active runtime mode and provides permission helpers."""

    def __init__(self, mode: RuntimeMode | None = None) -> None:
        self.mode = mode if mode is not None else get_current_mode()

    def can_create_intent(self) -> bool:
        """Intent creation is only permitted in SIMULATION or PAPER modes."""
        return self.mode in (RuntimeMode.SIMULATION, RuntimeMode.PAPER)

    def can_simulate(self) -> bool:
        """Simulation is only permitted in SIMULATION mode."""
        return self.mode == RuntimeMode.SIMULATION

    def can_paper_trade(self) -> bool:
        """Paper trading is only permitted in PAPER mode."""
        return self.mode == RuntimeMode.PAPER

    def can_submit(self) -> bool:
        """Submission is ALWAYS blocked in Phase 45."""
        return False

    def __repr__(self) -> str:
        return f"ModeContext(mode={self.mode.value!r})"
