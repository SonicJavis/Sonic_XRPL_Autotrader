"""Tests for normalizers."""
from __future__ import annotations
import pytest
from sonic_xrpl.providers.normalizers import (
    normalize_account,
    normalize_currency,
    normalize_asset_key,
    parse_asset_key,
    normalize_ledger_index,
    normalize_tx_hash,
    NormalizedAssetKey,
)


def test_normalize_account_valid():
    assert normalize_account("rTrader1111111111111111111111111111") == "rTrader1111111111111111111111111111"


def test_normalize_account_strips_whitespace():
    assert normalize_account("  rTrader  ") == "rTrader"


def test_normalize_account_empty_raises():
    with pytest.raises(ValueError):
        normalize_account("")


def test_normalize_currency_uppercase():
    assert normalize_currency("usd") == "USD"


def test_normalize_currency_empty_raises():
    with pytest.raises(ValueError):
        normalize_currency("")


def test_normalize_asset_key_xrp():
    key = normalize_asset_key("XRP", None)
    assert key.currency == "XRP"
    assert key.issuer is None
    assert str(key) == "XRP"


def test_normalize_asset_key_xrp_with_issuer_raises():
    with pytest.raises(ValueError):
        normalize_asset_key("XRP", "rSomeIssuer")


def test_normalize_asset_key_iou():
    key = normalize_asset_key("USD", "rIssuer1111111111111111111111111111")
    assert key.currency == "USD"
    assert key.issuer == "rIssuer1111111111111111111111111111"
    assert str(key) == "USD:rIssuer1111111111111111111111111111"


def test_normalize_asset_key_iou_no_issuer_raises():
    with pytest.raises(ValueError):
        normalize_asset_key("USD", None)


def test_parse_asset_key_xrp():
    key = parse_asset_key("XRP")
    assert key.currency == "XRP"
    assert key.issuer is None


def test_parse_asset_key_iou():
    key = parse_asset_key("USD:rIssuer1111111111111111111111111111")
    assert key.currency == "USD"
    assert key.issuer == "rIssuer1111111111111111111111111111"


def test_parse_asset_key_ambiguous_raises():
    with pytest.raises(ValueError):
        parse_asset_key("USD")


def test_normalize_ledger_index_valid():
    assert normalize_ledger_index(1000) == 1000
    assert normalize_ledger_index("1000") == 1000


def test_normalize_ledger_index_negative_raises():
    with pytest.raises(ValueError):
        normalize_ledger_index(-1)


def test_normalize_tx_hash_valid():
    h = "A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2C3D4E5F6A1B2"
    assert normalize_tx_hash(h) == h.upper()


def test_normalize_tx_hash_lowercase():
    h = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    assert normalize_tx_hash(h) == h.upper()


def test_normalize_tx_hash_wrong_length_raises():
    with pytest.raises(ValueError):
        normalize_tx_hash("ABCD")
