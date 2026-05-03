"""Tests for FailoverProvider enhancements."""
from __future__ import annotations
from sonic_xrpl.providers.failover import FailoverProvider
from sonic_xrpl.providers.mocks import MockLedgerProvider
from sonic_xrpl.core.errors import ProviderError
import pytest


def test_failover_get_account_lines():
    provider = FailoverProvider([MockLedgerProvider()])
    result = provider.get_account_lines("rTest")
    assert "lines" in result


def test_failover_tracks_reasons_on_failure():
    class FailingProvider(MockLedgerProvider):
        def get_server_info(self):
            raise RuntimeError("network error")

    provider = FailoverProvider([FailingProvider(), MockLedgerProvider()])
    result = provider.get_server_info()
    assert result is not None
    assert len(provider.last_failover_reasons) == 1
    assert "network error" in provider.last_failover_reasons[0]


def test_failover_all_fail_raises():
    class AlwaysFail(MockLedgerProvider):
        def get_server_info(self):
            raise RuntimeError("always fails")

    provider = FailoverProvider([AlwaysFail(), AlwaysFail()])
    with pytest.raises(ProviderError):
        provider.get_server_info()


def test_failover_reasons_reset_per_call():
    provider = FailoverProvider([MockLedgerProvider()])
    provider.get_server_info()
    provider.get_server_info()
    assert provider.last_failover_reasons == []
