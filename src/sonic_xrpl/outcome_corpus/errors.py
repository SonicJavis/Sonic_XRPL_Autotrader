from __future__ import annotations


class OutcomeCorpusError(ValueError):
    """Base error for Phase 52 outcome corpus handling."""


class OutcomeCorpusFixtureError(OutcomeCorpusError):
    """Raised when an outcome corpus fixture is malformed."""

