"""Market snapshot errors."""

from __future__ import annotations


class MarketSnapshotError(Exception):
    """Base error for market snapshot failures."""


class SnapshotBuildError(MarketSnapshotError):
    """Raised when snapshot cannot be built from fixture data."""


class FixtureHealthError(MarketSnapshotError):
    """Raised when fixture health check fails and strict mode is on."""


class CapabilityUnavailableWarning(UserWarning):
    """Warning when a requested capability is not enabled on mainnet."""
