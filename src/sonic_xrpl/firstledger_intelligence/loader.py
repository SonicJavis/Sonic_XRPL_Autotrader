from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.firstledger_intelligence.models import IntelligenceInput


def _to_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_firstledger_intelligence_inputs(path: str | Path) -> list[IntelligenceInput]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("candidates", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("Phase 59 intelligence fixture must be a list or a dict with a candidates list")

    results: list[IntelligenceInput] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        candidate_id = str(row.get("candidate_id") or "")
        issuer = str(row.get("issuer") or "")
        currency = str(row.get("currency") or "")
        symbol = str(row.get("symbol") or currency)
        tx_hash = str(row.get("tx_hash") or "")
        ledger_index = _to_int(row.get("ledger_index"))
        observed_at = str(row.get("observed_at") or "")
        source_url = str(row.get("source_url") or "")
        source_type = str(row.get("source_type") or "fixture")
        source_hash = str(row.get("source_hash") or "")
        limitations = tuple(row.get("limitations", [])) if isinstance(row.get("limitations", []), list) else tuple()

        results.append(
            IntelligenceInput(
                candidate_id=candidate_id,
                issuer=issuer,
                currency=currency,
                symbol=symbol,
                tx_hash=tx_hash,
                ledger_index=ledger_index,
                observed_at=observed_at,
                source_type=source_type,
                source_url=source_url,
                source_hash=source_hash,
                synthetic=_to_bool(row.get("synthetic", False)),
                source_backed=_to_bool(row.get("source_backed", True)),
                source_trust_known=_to_bool(row.get("source_trust_known", True)),
                metadata_status=str(row.get("metadata_status") or "missing"),
                metadata_mismatch=_to_bool(row.get("metadata_mismatch", False)),
                launch_quality=str(row.get("launch_quality") or "unknown"),
                holder_count=_to_int(row.get("holder_count")),
                top_holder_ratio=_to_float(row.get("top_holder_ratio")),
                dev_hold_ratio=_to_float(row.get("dev_hold_ratio")),
                issuer_hold_ratio=_to_float(row.get("issuer_hold_ratio")),
                liquidity_usd=_to_float(row.get("liquidity_usd")),
                freeze_enabled=None if row.get("freeze_enabled") is None else _to_bool(row.get("freeze_enabled")),
                clawback_enabled=None if row.get("clawback_enabled") is None else _to_bool(row.get("clawback_enabled")),
                same_symbol_different_issuer=_to_bool(row.get("same_symbol_different_issuer", False)),
                source_conflict=_to_bool(row.get("source_conflict", False)),
                stale_hours=_to_int(row.get("stale_hours")),
                malformed_source_record=_to_bool(row.get("malformed_source_record", False)),
                limitations=limitations,
            )
        )

    results.sort(key=lambda item: item.candidate_id)
    return results
