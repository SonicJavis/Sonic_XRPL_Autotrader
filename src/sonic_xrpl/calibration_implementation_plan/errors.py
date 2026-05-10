from __future__ import annotations


class CalibrationImplementationPlanError(ValueError):
    """Base error for Phase 56 implementation planning failures."""


class ImplementationInputError(CalibrationImplementationPlanError):
    """Raised when approval/change-request inputs are invalid."""
