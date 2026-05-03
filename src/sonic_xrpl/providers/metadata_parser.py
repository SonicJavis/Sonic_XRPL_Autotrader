"""Offline XRPL transaction metadata parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AffectedNode:
    node_type: str  # "CreatedNode" | "ModifiedNode" | "DeletedNode"
    ledger_entry_type: str
    ledger_index: str
    final_fields: dict[str, Any] | None
    previous_fields: dict[str, Any] | None
    new_fields: dict[str, Any] | None


@dataclass
class MetadataParseResult:
    transaction_result: str
    affected_nodes: list[AffectedNode]
    delivered_amount: str | dict[str, Any] | None
    has_metadata: bool
    limitations: list[str] = field(default_factory=list)


def detect_node_type(node_key: str) -> str:
    if node_key == "CreatedNode":
        return "CreatedNode"
    if node_key == "ModifiedNode":
        return "ModifiedNode"
    if node_key == "DeletedNode":
        return "DeletedNode"
    return node_key


def extract_affected_nodes(metadata: dict[str, Any]) -> list[AffectedNode]:
    nodes = []
    for raw_node in metadata.get("AffectedNodes", []):
        for node_key in ("CreatedNode", "ModifiedNode", "DeletedNode"):
            if node_key in raw_node:
                inner = raw_node[node_key]
                nodes.append(AffectedNode(
                    node_type=detect_node_type(node_key),
                    ledger_entry_type=inner.get("LedgerEntryType", ""),
                    ledger_index=inner.get("LedgerIndex", ""),
                    final_fields=inner.get("FinalFields"),
                    previous_fields=inner.get("PreviousFields"),
                    new_fields=inner.get("NewFields"),
                ))
                break
    return nodes


def get_delivered_amount(
    metadata: dict[str, Any],
    transaction: dict[str, Any] | None = None,
) -> str | dict[str, Any] | None:
    """Return delivered_amount preferring metadata over transaction.Amount."""
    if metadata:
        da = metadata.get("delivered_amount")
        if da is not None:
            return da
    if transaction:
        return transaction.get("Amount")
    return None


def is_sufficient_truth(metadata: dict[str, Any]) -> bool:
    """Return False if tesSUCCESS but no metadata nodes — not sufficient truth."""
    if not metadata:
        return False
    result = metadata.get("TransactionResult", "")
    if result == "tesSUCCESS" and not metadata.get("AffectedNodes"):
        return False
    return result == "tesSUCCESS"


def parse_metadata(metadata: dict[str, Any]) -> MetadataParseResult:
    """Parse XRPL transaction metadata into a structured result."""
    limitations: list[str] = []

    if not metadata:
        return MetadataParseResult(
            transaction_result="",
            affected_nodes=[],
            delivered_amount=None,
            has_metadata=False,
            limitations=["no metadata provided"],
        )

    tx_result = metadata.get("TransactionResult", "")
    nodes = extract_affected_nodes(metadata)
    da = get_delivered_amount(metadata)

    if not nodes and tx_result == "tesSUCCESS":
        limitations.append("tesSUCCESS with no AffectedNodes — not sufficient truth for PnL attribution")

    return MetadataParseResult(
        transaction_result=tx_result,
        affected_nodes=nodes,
        delivered_amount=da,
        has_metadata=True,
        limitations=limitations,
    )
