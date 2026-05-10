from __future__ import annotations

from sonic_xrpl.reconciliation.intent_ledger import reconcile_intent_to_ledger


def test_reconcile_marks_partial_when_validated_amount_differs() -> None:
    record = reconcile_intent_to_ledger(
        intent_id="intent-1",
        tx_hash="ABC123",
        expected_base_drops="100",
        expected_quote_value="10",
        metadata={
            "delivered_amount": {"value": "60"},
            "validated_quote_value": "6",
            "owner_funds": "1000",
        },
    )
    assert record.partial_fill is True
    assert record.status == "partial"
    assert "partial_fill_detected" in record.limitations


def test_reconcile_marks_matched_when_amount_equal() -> None:
    record = reconcile_intent_to_ledger(
        intent_id="intent-2",
        tx_hash="DEF456",
        expected_base_drops="75",
        expected_quote_value="8",
        metadata={
            "delivered_amount": {"value": "75"},
            "validated_quote_value": "8",
            "owner_funds": "999",
        },
    )
    assert record.partial_fill is False
    assert record.status == "matched"
    assert record.limitations == ()
