"""Error hierarchy for Sonic XRPL V2."""

from __future__ import annotations


class SonicBaseError(Exception):
    """Base exception for all Sonic XRPL V2 errors."""


class LiveTradingDisabledError(SonicBaseError):
    """Raised when live trading or submission is attempted. Always blocked in Phase 45."""


class ModeViolationError(SonicBaseError):
    """Raised when an operation is attempted in a disallowed runtime mode."""


class CapabilityNotAvailableError(SonicBaseError):
    """Raised when a required XRPL protocol capability is not available."""


class ProviderError(SonicBaseError):
    """Raised for provider connectivity or data errors."""


class SimulationError(SonicBaseError):
    """Raised for simulation model errors."""


class ReconciliationError(SonicBaseError):
    """Raised for reconciliation failures."""


class SafetyViolationError(SonicBaseError):
    """Raised when a safety scan finds a blocked pattern in runtime code."""


class ConfigurationError(SonicBaseError):
    """Raised for invalid configuration."""
