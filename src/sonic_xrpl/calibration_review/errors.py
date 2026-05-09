from __future__ import annotations


class CalibrationReviewError(Exception):
    """Base error for Phase 53 calibration readiness review."""


class CalibrationReviewFixtureError(CalibrationReviewError):
    """Raised when a calibration review input fixture is invalid."""
