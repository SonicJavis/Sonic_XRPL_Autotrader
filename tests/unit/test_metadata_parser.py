"""Tests for metadata_parser."""
from __future__ import annotations
import json
from pathlib import Path
from sonic_xrpl.providers.metadata_parser import (
    parse_metadata,
    extract_affected_nodes,
    get_delivered_amount,
    is_sufficient_truth,
)

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl" / "metadata"


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_parse_payment_partial_metadata():
    metadata = _load("payment_partial_metadata.json")
    result = parse_metadata(metadata)
    assert result.transaction_result == "tesSUCCESS"
    assert result.has_metadata is True
    assert result.delivered_amount is not None


def test_parse_empty_metadata():
    result = parse_metadata({})
    assert result.has_metadata is False
    assert "no metadata provided" in result.limitations


def test_parse_tessuccess_no_nodes_limitation():
    metadata = {"TransactionResult": "tesSUCCESS", "AffectedNodes": []}
    result = parse_metadata(metadata)
    assert any("not sufficient truth" in lim for lim in result.limitations)


def test_extract_affected_nodes_amm_create():
    metadata = _load("amm_create_metadata.json")
    nodes = extract_affected_nodes(metadata)
    assert len(nodes) == 1
    assert nodes[0].node_type == "CreatedNode"
    assert nodes[0].ledger_entry_type == "AMM"


def test_get_delivered_amount_from_metadata():
    metadata = {"delivered_amount": {"currency": "USD", "value": "50"}}
    da = get_delivered_amount(metadata)
    assert da == {"currency": "USD", "value": "50"}


def test_get_delivered_amount_falls_back_to_transaction():
    metadata = {}
    tx = {"Amount": "1000000"}
    da = get_delivered_amount(metadata, tx)
    assert da == "1000000"


def test_is_sufficient_truth_no_nodes():
    metadata = {"TransactionResult": "tesSUCCESS", "AffectedNodes": []}
    assert is_sufficient_truth(metadata) is False


def test_is_sufficient_truth_with_nodes():
    metadata = {
        "TransactionResult": "tesSUCCESS",
        "AffectedNodes": [{"ModifiedNode": {"LedgerEntryType": "AccountRoot", "LedgerIndex": "X", "FinalFields": {}, "PreviousFields": {}}}]
    }
    assert is_sufficient_truth(metadata) is True
