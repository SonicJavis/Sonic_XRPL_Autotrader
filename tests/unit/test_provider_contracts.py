"""Tests for provider contracts."""

from __future__ import annotations

import pytest
from sonic_xrpl.core.errors import LiveTradingDisabledError
from sonic_xrpl.providers.mocks import (
    MockLedgerProvider,
    MockHistoricalProvider,
    MockSubmissionProvider,
)
from sonic_xrpl.providers.base import LedgerProvider, HistoricalProvider, SubmissionProvider


def test_mock_ledger_provider_is_ledger_provider():
    """MockLedgerProvider is a LedgerProvider."""
    assert isinstance(MockLedgerProvider(), LedgerProvider)


def test_mock_historical_provider_is_historical_provider():
    """MockHistoricalProvider is a HistoricalProvider."""
    assert isinstance(MockHistoricalProvider(), HistoricalProvider)


def test_mock_submission_provider_is_submission_provider():
    """MockSubmissionProvider is a SubmissionProvider."""
    assert isinstance(MockSubmissionProvider(), SubmissionProvider)


def test_mock_ledger_provider_get_server_info():
    """MockLedgerProvider.get_server_info() returns data."""
    provider = MockLedgerProvider()
    info = provider.get_server_info()
    assert "info" in info
    assert info["status"] == "success"


def test_mock_ledger_provider_validated_ledger():
    """MockLedgerProvider.get_latest_validated_ledger() returns validated ledger."""
    provider = MockLedgerProvider()
    ledger = provider.get_latest_validated_ledger()
    assert ledger["validated"] is True
    assert ledger["ledger_index"] > 0


def test_mock_ledger_provider_account_info():
    """MockLedgerProvider.get_account_info() returns account data."""
    provider = MockLedgerProvider()
    info = provider.get_account_info("rTestAccount")
    assert info["account_data"]["Account"] == "rTestAccount"


def test_mock_submission_provider_submit_raises():
    """MockSubmissionProvider.submit() always raises LiveTradingDisabledError."""
    provider = MockSubmissionProvider()
    with pytest.raises(LiveTradingDisabledError):
        provider.submit(tx_blob="DEADBEEF")


def test_mock_submission_provider_submit_and_wait_raises():
    """MockSubmissionProvider.submit_and_wait() always raises LiveTradingDisabledError."""
    provider = MockSubmissionProvider()
    with pytest.raises(LiveTradingDisabledError):
        provider.submit_and_wait(tx_blob="DEADBEEF")
