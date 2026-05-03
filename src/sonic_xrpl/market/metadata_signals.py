"""Metadata signals extractor — Phase 47.

Wraps Phase 46 metadata_parser and balance_changes to build MetadataSignal objects.

Rules:
- Do not infer fills or profit.
- Do not assume tesSUCCESS is enough without metadata.
- delivered_amount must be surfaced for Payment transactions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sonic_xrpl.providers.metadata_parser import (
    parse_metadata,
    is_sufficient_truth,
)
from sonic_xrpl.providers.balance_changes import extract_balance_changes
from sonic_xrpl.market.models import MetadataSignal


def _node_types_changed(affected_nodes: list) -> list[str]:
    """Return distinct LedgerEntryTypes that were modified."""
    seen: list[str] = []
    for node in affected_nodes:
        entry_type = node.ledger_entry_type
        if entry_type and entry_type not in seen:
            seen.append(entry_type)
    return seen


def _classify_signal_flags(
    tx_type: str,
    delivered_amount: Any,
    affected_nodes: list,
    node_types: list[str],
) -> list[str]:
    """Classify signal flags based on metadata contents."""
    flags: list[str] = []

    if delivered_amount is None and tx_type == "Payment":
        flags.append("missing_delivered_amount")

    if "Payment" in tx_type and delivered_amount is not None:
        flags.append("delivered_amount_present")

    if not is_sufficient_truth({"TransactionResult": "tesSUCCESS", "AffectedNodes": affected_nodes}):
        flags.append("insufficient_truth")

    if "RippleState" in node_types:
        flags.append("trustline_changed")

    if "AMM" in node_types or "AMMState" in node_types:
        flags.append("amm_changed")

    if "Offer" in node_types:
        flags.append("offer_changed")

    if "AccountRoot" in node_types:
        flags.append("account_balance_changed")

    if "MPToken" in node_types or "MPTokenIssuance" in node_types:
        flags.append("mpt_changed")

    return flags


def build_metadata_signal(
    tx_hash: str,
    tx_type: str,
    ledger_index: int,
    metadata: dict[str, Any],
) -> MetadataSignal:
    """Build a MetadataSignal from raw XRPL transaction metadata."""
    limitations: list[str] = []

    if not metadata:
        return MetadataSignal(
            tx_hash=tx_hash,
            tx_type=tx_type,
            ledger_index=ledger_index,
            delivered_amount=None,
            affected_node_count=0,
            balance_changes=[],
            signal_flags=["no_metadata"],
            limitations=["no metadata provided"],
        )

    result = parse_metadata(metadata)
    limitations.extend(result.limitations)

    node_types = _node_types_changed(result.affected_nodes)
    signal_flags = _classify_signal_flags(
        tx_type,
        result.delivered_amount,
        result.affected_nodes,
        node_types,
    )

    balance_changes = extract_balance_changes(metadata)
    bc_dicts = [
        {
            "account": bc.account,
            "currency": bc.currency,
            "issuer": bc.issuer,
            "value": bc.value,
            "asset_key": bc.asset_key,
        }
        for bc in balance_changes
    ]

    if not result.has_metadata:
        limitations.append("metadata object missing")

    return MetadataSignal(
        tx_hash=tx_hash,
        tx_type=tx_type,
        ledger_index=ledger_index,
        delivered_amount=result.delivered_amount,
        affected_node_count=len(result.affected_nodes),
        balance_changes=bc_dicts,
        signal_flags=signal_flags,
        limitations=limitations,
    )


def build_signals_from_fixture_metadata(
    metadata_dir: Path,
) -> tuple[list[MetadataSignal], list[str]]:
    """Load all metadata JSON files from a directory and build MetadataSignals.

    Returns (signals, warnings).
    """
    signals: list[MetadataSignal] = []
    warnings: list[str] = []

    if not metadata_dir.exists():
        return [], ["metadata directory does not exist"]

    import json

    for f in sorted(metadata_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except Exception as exc:
            warnings.append(f"Failed to parse {f.name}: {exc}")
            continue

        tx_hash = data.get("hash", f.stem)
        tx_type = data.get("TransactionType", data.get("transaction_type", "Unknown"))
        ledger_index = data.get("ledger_index", 0)
        meta = data.get("meta", data.get("metaData", data))

        signal = build_metadata_signal(tx_hash, tx_type, ledger_index, meta)
        signals.append(signal)

    return signals, warnings
