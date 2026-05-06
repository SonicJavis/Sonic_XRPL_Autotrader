"""Evidence extraction helpers for Phase 49 FirstLedger signals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from execution_prototype.discovery.firstledger_reader import parse_firstledger_fixture
from sonic_xrpl.signals.models import FirstLedgerCandidateEvidence, SignalEvidence

REQUIRED_FIELDS = ("issuer", "currency", "tx_hash", "ledger_index", "source", "observed_at")
_FIELD_ALIASES = {
    "issuer": ("issuer", "issuer_address", "account"),
    "currency": ("currency", "currency_code", "token", "symbol"),
    "tx_hash": ("tx_hash", "hash", "transaction_hash"),
    "ledger_index": ("ledger_index", "ledger", "validated_ledger_index"),
    "source": ("source_url", "source", "source_identifier"),
    "observed_at": ("observed_at", "timestamp"),
}


def stable_hash(value: Any) -> str:
    """Return a deterministic SHA-256 hash for arbitrary JSON-like evidence."""
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: Any, length: int = 24) -> str:
    """Return a stable, human-scoped identifier."""
    joined = "|".join(str(part or "") for part in parts)
    return f"{prefix}_{hashlib.sha256(joined.encode('utf-8')).hexdigest()[:length]}"


def _first_present(row: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return ""


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "validated", "success"}
    return bool(value)


def _as_int_or_none(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def load_candidate_rows(path: str | Path) -> list[Mapping[str, Any]]:
    """Load deterministic fixture rows without any network access."""
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict):
        rows = data.get("candidates", [])
    else:
        rows = data
    if not isinstance(rows, list):
        raise ValueError("FirstLedger fixture must be a list or contain a candidates list")
    return [row for row in rows if isinstance(row, Mapping)]


def evidence_from_rows(rows: Iterable[Mapping[str, Any]]) -> list[FirstLedgerCandidateEvidence]:
    """Build evidence from raw source-backed rows and the strict parser boundary.

    The Phase 48 parser remains the source for accepted discovery events. Rows
    that fail the strict parser are still represented as limited evidence so the
    classifier can return INSUFFICIENT_EVIDENCE instead of inventing data.
    """
    row_list = list(rows)
    parsed_by_tx = {event.tx_hash: event for event in parse_firstledger_fixture(row_list)}
    evidence: list[FirstLedgerCandidateEvidence] = []
    for row in row_list:
        issuer = str(_first_present(row, _FIELD_ALIASES["issuer"])).strip()
        currency = str(_first_present(row, _FIELD_ALIASES["currency"])).strip()
        tx_hash = str(_first_present(row, _FIELD_ALIASES["tx_hash"])).strip()
        ledger_index = _as_int_or_none(_first_present(row, _FIELD_ALIASES["ledger_index"]))
        source_url = str(_first_present(row, _FIELD_ALIASES["source"])).strip()
        observed_at = str(_first_present(row, _FIELD_ALIASES["observed_at"])).strip()
        metadata_present = _as_bool(row.get("metadata_present", row.get("has_metadata", False)))
        validated = _as_bool(row.get("validated", row.get("is_validated", False)))
        synthetic = _as_bool(row.get("synthetic", False))

        present = []
        missing = []
        values = {
            "issuer": issuer,
            "currency": currency,
            "tx_hash": tx_hash,
            "ledger_index": ledger_index,
            "source": source_url,
            "observed_at": observed_at,
        }
        for field, value in values.items():
            (present if value not in (None, "") else missing).append(field)

        limitations = list(row.get("limitations", [])) if isinstance(row.get("limitations", []), list) else []
        if not observed_at and "observed_at_missing" not in limitations:
            limitations.append("observed_at_missing")
        if not metadata_present:
            limitations.append("metadata_missing_signal_is_low_confidence")
        if not validated:
            limitations.append("not_validated_do_not_treat_as_final")
        if synthetic:
            limitations.append("synthetic_fixture_not_real_market_data")
        if missing:
            limitations.append("missing_required_fields:" + ",".join(sorted(missing)))

        parsed = parsed_by_tx.get(tx_hash)
        candidate_id = str(row.get("candidate_id") or (parsed.event_id if parsed else stable_id("flc", issuer, currency, tx_hash, ledger_index)))
        evidence.append(
            FirstLedgerCandidateEvidence(
                candidate_id=candidate_id,
                observed_at=observed_at,
                source_url=source_url,
                source_type=str(row.get("source_type") or "fixture"),
                source_hash=str(row.get("source_hash") or stable_hash(row)),
                issuer=issuer,
                currency=currency,
                tx_hash=tx_hash,
                ledger_index=ledger_index,
                metadata_status="validated" if metadata_present and validated else ("present_unvalidated" if metadata_present else "missing"),
                validation_status="validated" if validated else "unvalidated",
                limitations=tuple(dict.fromkeys(limitations)),
                raw_fields_present=tuple(sorted(present)),
                raw_fields_missing=tuple(sorted(missing)),
                synthetic=synthetic,
            )
        )
    evidence.sort(key=lambda item: (item.ledger_index or 0, item.tx_hash, item.candidate_id))
    return evidence


def atomic_signal_evidence(candidate: FirstLedgerCandidateEvidence) -> list[SignalEvidence]:
    """Create explainable evidence atoms without fabricating missing fields."""
    atoms = []
    for field in ("issuer", "currency", "tx_hash", "ledger_index", "source_url", "observed_at", "metadata_status", "validation_status"):
        value = getattr(candidate, field)
        source_backed = value not in (None, "")
        atoms.append(SignalEvidence(
            evidence_id=stable_id("ev", candidate.candidate_id, field, value),
            source=candidate.source_url or candidate.source_type or "unknown_source",
            field=field,
            value=value if source_backed else "unknown",
            confidence=100 if source_backed else 0,
            limitation="" if source_backed else f"{field}_missing",
            source_backed=source_backed,
        ))
    return atoms
