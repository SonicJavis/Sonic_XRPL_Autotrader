"""Tests for balance_changes."""
from __future__ import annotations
import json
from pathlib import Path
from sonic_xrpl.providers.balance_changes import extract_balance_changes, BalanceChange

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl" / "metadata"


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_xrp_balance_change_extracted():
    metadata = _load("payment_partial_metadata.json")
    changes = extract_balance_changes(metadata)
    xrp_changes = [c for c in changes if c.currency == "XRP"]
    assert len(xrp_changes) == 1
    assert int(xrp_changes[0].value) == -100000000


def test_usd_balance_change_extracted():
    metadata = _load("payment_partial_metadata.json")
    changes = extract_balance_changes(metadata)
    usd_changes = [c for c in changes if c.currency == "USD"]
    assert len(usd_changes) == 1
    assert usd_changes[0].issuer == "rIssuer1111111111111111111111111111"


def test_empty_metadata_returns_empty():
    changes = extract_balance_changes({})
    assert changes == []


def test_no_affected_nodes_returns_empty():
    metadata = {"TransactionResult": "tesSUCCESS", "AffectedNodes": []}
    changes = extract_balance_changes(metadata)
    assert changes == []


def test_asset_key_xrp():
    change = BalanceChange(account="rX", currency="XRP", issuer=None, value="-1000")
    assert change.asset_key == "XRP"


def test_asset_key_iou():
    change = BalanceChange(account="rX", currency="USD", issuer="rIssuer", value="50.0")
    assert change.asset_key == "USD:rIssuer"
