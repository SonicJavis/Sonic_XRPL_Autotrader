"""Tests for FixtureLedgerProvider."""
from __future__ import annotations
from pathlib import Path
import pytest
from sonic_xrpl.providers.fixture_ledger import FixtureLedgerProvider
from sonic_xrpl.providers.errors import FixtureMissingError
from sonic_xrpl.providers.base import ProviderType

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl"
TRADER = "rTrader1111111111111111111111111111"
ISSUER = "rIssuer1111111111111111111111111111"


@pytest.fixture
def provider():
    return FixtureLedgerProvider(FIXTURE_DIR)


def test_provider_type_is_fixture(provider):
    assert provider.provider_type == ProviderType.FIXTURE


def test_get_server_info(provider):
    info = provider.get_server_info()
    assert info["info"]["build_version"] == "1.12.0-fixture"
    assert info["info"]["server_state"] == "full"


def test_get_latest_validated_ledger(provider):
    ledger = provider.get_latest_validated_ledger()
    assert ledger["ledger_index"] == 1001
    assert ledger["validated"] is True


def test_get_account_info_trader(provider):
    info = provider.get_account_info(TRADER)
    assert info["account_data"]["Account"] == TRADER
    assert info["account_data"]["Balance"] == "1000000000"


def test_get_account_info_issuer(provider):
    info = provider.get_account_info(ISSUER)
    assert info["account_data"]["Account"] == ISSUER


def test_get_account_info_missing_raises(provider):
    with pytest.raises(FixtureMissingError):
        provider.get_account_info("rNoSuchAccount11111111111111111111")


def test_get_account_lines(provider):
    result = provider.get_account_lines(TRADER)
    assert result["account"] == TRADER
    assert len(result["lines"]) == 1
    assert result["lines"][0]["currency"] == "USD"


def test_get_account_tx_filtering(provider):
    result = provider.get_account_tx(TRADER)
    assert result["account"] == TRADER
    assert len(result["transactions"]) == 2


def test_get_account_tx_ledger_min(provider):
    result = provider.get_account_tx(TRADER, ledger_min=1001)
    txs = result["transactions"]
    assert len(txs) == 1
    assert txs[0]["ledger_index"] == 1001


def test_get_orderbook(provider):
    ob = provider.get_orderbook(taker_gets="XRP", taker_pays="USD")
    assert "offers" in ob
    assert len(ob["offers"]) == 1


def test_get_amm_info(provider):
    amm = provider.get_amm_info(asset_a="XRP", asset_b="USD")
    assert "amm" in amm
    assert amm["amm"]["trading_fee"] == 500


def test_get_mpt_holders(provider):
    result = provider.get_mpt_holders(mpt_issuance_id="0000000000000000000000000000000000000000000000000000000000000001")
    assert "holders" in result
    assert len(result["holders"]) == 1


def test_get_ledger_entry_by_index(provider):
    entry = provider.get_ledger_entry(ledger_index=1000)
    assert entry["ledger_index"] == 1000


def test_close_does_not_raise(provider):
    provider.close()


def test_fixture_missing_raises_not_mock(provider):
    """FixtureLedgerProvider must raise FixtureMissingError, not return mock data."""
    with pytest.raises(FixtureMissingError):
        provider.get_account_info("rNoSuchAccount11111111111111111111")
