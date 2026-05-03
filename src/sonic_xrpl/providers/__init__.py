"""Provider abstractions: LedgerProvider, HistoricalProvider, SubmissionProvider.

Phase 46: Added fixture-based providers.
"""

from sonic_xrpl.providers.base import LedgerProvider, HistoricalProvider, SubmissionProvider, ProviderType
from sonic_xrpl.providers.mocks import MockLedgerProvider, MockHistoricalProvider, MockSubmissionProvider
from sonic_xrpl.providers.failover import FailoverProvider
from sonic_xrpl.providers.fixture_ledger import FixtureLedgerProvider
from sonic_xrpl.providers.fixture_store import FixtureStore
from sonic_xrpl.providers.fixture_market_data import FixtureMarketDataProvider
from sonic_xrpl.providers.errors import (
    ProviderUnavailableError,
    DataQualityError,
    FixtureMissingError,
    FixtureCorruptError,
    StaleFixtureError,
)

__all__ = [
    "LedgerProvider",
    "HistoricalProvider",
    "SubmissionProvider",
    "ProviderType",
    "MockLedgerProvider",
    "MockHistoricalProvider",
    "MockSubmissionProvider",
    "FailoverProvider",
    "FixtureLedgerProvider",
    "FixtureStore",
    "FixtureMarketDataProvider",
    "ProviderUnavailableError",
    "DataQualityError",
    "FixtureMissingError",
    "FixtureCorruptError",
    "StaleFixtureError",
]
