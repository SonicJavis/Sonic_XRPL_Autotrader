from __future__ import annotations


class OutcomeError(ValueError):
    """Base error for deterministic paper outcome processing."""


class OutcomeFixtureError(OutcomeError):
    """Raised when a paper outcome fixture cannot be parsed."""
