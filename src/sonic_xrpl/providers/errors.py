"""Provider-specific error types."""

from __future__ import annotations

from sonic_xrpl.core.errors import ProviderError


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is unavailable."""


class DataQualityError(ProviderError):
    """Raised when provider data quality is insufficient."""


class FixtureMissingError(ProviderError):
    """Raised when a required fixture file is not found."""


class FixtureCorruptError(ProviderError):
    """Raised when a fixture file cannot be parsed."""


class StaleFixtureError(ProviderError):
    """Raised when fixture data is outside the expected ledger range."""
