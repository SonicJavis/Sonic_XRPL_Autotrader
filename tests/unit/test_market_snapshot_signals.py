"""Tests for metadata signals builder."""

from __future__ import annotations

import pytest
from sonic_xrpl.market.metadata_signals import build_metadata_signal, build_signals_from_fixture_metadata
from pathlib import Path

FIXTURE_METADATA_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl" / "metadata"

_PAYMENT_METADATA = {
    "TransactionResult": "tesSUCCESS",
    "delivered_amount": {"currency": "USD", "issuer": "rIssuer", "value": "10"},
    "AffectedNodes": [
        {
            "ModifiedNode": {
                "LedgerEntryType": "AccountRoot",
                "LedgerIndex": "ABC",
                "FinalFields": {"Account": "rTrader", "Balance": "99000000"},
                "PreviousFields": {"Balance": "100000000"},
            }
        }
    ],
}


class TestMetadataSignal:
    def test_basic_payment_signal(self):
        sig = build_metadata_signal("TXHASH001", "Payment", 1000, _PAYMENT_METADATA)
        assert sig.tx_hash == "TXHASH001"
        assert sig.tx_type == "Payment"
        assert sig.ledger_index == 1000
        assert sig.delivered_amount is not None
        assert sig.affected_node_count == 1

    def test_delivered_amount_present_flag(self):
        sig = build_metadata_signal("TXHASH001", "Payment", 1000, _PAYMENT_METADATA)
        assert "delivered_amount_present" in sig.signal_flags

    def test_account_balance_changed_flag(self):
        sig = build_metadata_signal("TXHASH001", "Payment", 1000, _PAYMENT_METADATA)
        assert "account_balance_changed" in sig.signal_flags

    def test_no_metadata(self):
        sig = build_metadata_signal("TX_EMPTY", "Payment", 1000, {})
        assert sig.affected_node_count == 0
        assert "no_metadata" in sig.signal_flags
        assert sig.delivered_amount is None

    def test_missing_delivered_amount_payment(self):
        meta = {
            "TransactionResult": "tesSUCCESS",
            "AffectedNodes": [],
        }
        sig = build_metadata_signal("TX2", "Payment", 1000, meta)
        assert "missing_delivered_amount" in sig.signal_flags

    def test_insufficient_truth_flag(self):
        meta = {
            "TransactionResult": "tesSUCCESS",
            "AffectedNodes": [],
        }
        sig = build_metadata_signal("TX3", "OfferCreate", 1000, meta)
        assert "insufficient_truth" in sig.signal_flags

    def test_trustline_changed_flag(self):
        meta = {
            "TransactionResult": "tesSUCCESS",
            "AffectedNodes": [
                {
                    "ModifiedNode": {
                        "LedgerEntryType": "RippleState",
                        "LedgerIndex": "DEF",
                        "FinalFields": {"Balance": {"currency": "USD", "issuer": "rI", "value": "50"}},
                        "PreviousFields": {"Balance": {"currency": "USD", "issuer": "rI", "value": "40"}},
                    }
                }
            ],
        }
        sig = build_metadata_signal("TX4", "Payment", 1000, meta)
        assert "trustline_changed" in sig.signal_flags

    def test_frozen_dataclass(self):
        sig = build_metadata_signal("TX", "Payment", 1000, _PAYMENT_METADATA)
        with pytest.raises((TypeError, AttributeError)):
            sig.tx_hash = "new"  # type: ignore[misc]


class TestBuildSignalsFromFixture:
    def test_loads_from_fixture_dir(self):
        signals, warnings = build_signals_from_fixture_metadata(FIXTURE_METADATA_DIR)
        assert isinstance(signals, list)
        assert isinstance(warnings, list)
        # At least one metadata file should be loaded
        assert len(signals) >= 1

    def test_nonexistent_dir_returns_warning(self):
        signals, warnings = build_signals_from_fixture_metadata(Path("/nonexistent/path"))
        assert signals == []
        assert len(warnings) >= 1
