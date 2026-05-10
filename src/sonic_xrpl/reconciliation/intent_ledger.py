"""Intent to ledger reconciliation primitives (paper to future-live bridge)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntentLedgerRecord:
    intent_id: str
    tx_hash: str
    expected_base_drops: str
    expected_quote_value: str
    validated_base_drops: str
    validated_quote_value: str
    owner_funds: str | None
    partial_fill: bool
    status: str
    limitations: tuple[str, ...] = field(default_factory=tuple)


def reconcile_intent_to_ledger(
    *,
    intent_id: str,
    tx_hash: str,
    expected_base_drops: str,
    expected_quote_value: str,
    metadata: dict[str, object],
) -> IntentLedgerRecord:
    delivered = metadata.get("delivered_amount", {})
    if not isinstance(delivered, dict):
        delivered = {}

    validated_base = str(delivered.get("value", "0"))
    validated_quote = str(metadata.get("validated_quote_value", "0"))
    owner_funds = metadata.get("owner_funds")
    owner_funds_text = None if owner_funds is None else str(owner_funds)

    partial_fill = validated_base != str(expected_base_drops)
    status = "partial" if partial_fill else "matched"
    limitations: list[str] = []
    if owner_funds_text is None:
        limitations.append("owner_funds_unavailable")
    if partial_fill:
        limitations.append("partial_fill_detected")

    return IntentLedgerRecord(
        intent_id=intent_id,
        tx_hash=tx_hash,
        expected_base_drops=str(expected_base_drops),
        expected_quote_value=str(expected_quote_value),
        validated_base_drops=validated_base,
        validated_quote_value=validated_quote,
        owner_funds=owner_funds_text,
        partial_fill=partial_fill,
        status=status,
        limitations=tuple(limitations),
    )
