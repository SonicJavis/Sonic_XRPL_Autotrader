"""Tests for FixtureMarketDataProvider."""
from __future__ import annotations
from pathlib import Path
import pytest
from sonic_xrpl.providers.fixture_store import FixtureStore
from sonic_xrpl.providers.fixture_market_data import FixtureMarketDataProvider

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl"


@pytest.fixture
def provider():
    store = FixtureStore(FIXTURE_DIR)
    return FixtureMarketDataProvider(store)


def test_get_orderbook_snapshot(provider):
    ob = provider.get_orderbook_snapshot("XRP", "USD")
    assert "offers" in ob


def test_get_amm_snapshot(provider):
    amm = provider.get_amm_snapshot("XRP", "USD")
    assert "amm" in amm


def test_get_price_series_returns_limitation(provider):
    result = provider.get_price_series("XRP")
    assert "limitation" in result
    assert result["data"] == []


def test_get_liquidity_series_returns_limitation(provider):
    result = provider.get_liquidity_series("XRP")
    assert "limitation" in result
    assert result["data"] == []
