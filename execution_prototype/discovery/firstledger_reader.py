from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from execution_prototype.discovery.models import RawDiscoveryEvent


SUPPORTED_EVENT_TYPES = {
    "trustline_created",
    "amm_created",
    "issuer_activity",
    "offer_activity_low_confidence",
}


def _first_present(row: Mapping[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "validated", "success"}
    if value is None:
        return default
    return bool(value)


def _normalise_event_type(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    aliases = {
        "trustline": "trustline_created",
        "trustset": "trustline_created",
        "trust_set": "trustline_created",
        "amm": "amm_created",
        "ammcreate": "amm_created",
        "amm_create": "amm_created",
        "issuer": "issuer_activity",
        "offer": "offer_activity_low_confidence",
        "offercreate": "offer_activity_low_confidence",
        "offer_create": "offer_activity_low_confidence",
    }
    return aliases.get(value, value)


def _stable_event_id(*parts: Any) -> str:
    joined = "|".join(str(part or "") for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]


def parse_firstledger_fixture(data: Iterable[Mapping[str, Any]]) -> List[RawDiscoveryEvent]:
    """Parse source-backed FirstLedger fixture rows into discovery events.

    This function is deliberately offline and deterministic. It does not scrape
    FirstLedger, does not call XRPL, and does not invent token launches. Rows
    that do not contain enough provenance to support a discovery event are
    ignored rather than filled with fake values.

    Accepted row keys are intentionally broad so fixture exporters can use
    either FirstLedger-like names or normalized adapter names:
    - event_type/type/kind/transaction_type
    - issuer/issuer_address/account
    - currency/currency_code/token/symbol
    - ledger_index/ledger/validated_ledger_index
    - tx_hash/hash/transaction_hash
    - validated/is_validated
    - metadata_present/has_metadata
    - observed_at/timestamp
    """

    events: List[RawDiscoveryEvent] = []
    for row in data:
        event_type = _normalise_event_type(_first_present(row, "event_type", "type", "kind", "transaction_type"))
        issuer = str(_first_present(row, "issuer", "issuer_address", "account") or "").strip()
        currency_code = str(_first_present(row, "currency_code", "currency", "token", "symbol") or "").strip()
        ledger_index = _as_int(_first_present(row, "ledger_index", "ledger", "validated_ledger_index"), 0)
        tx_hash = str(_first_present(row, "tx_hash", "hash", "transaction_hash") or "").strip()
        validated = _as_bool(_first_present(row, "validated", "is_validated"), False)
        metadata_present = _as_bool(_first_present(row, "metadata_present", "has_metadata"), False)
        observed_at = str(_first_present(row, "observed_at", "timestamp") or "").strip()

        limitations: List[str] = []
        if event_type not in SUPPORTED_EVENT_TYPES:
            continue
        if not issuer:
            continue
        if not currency_code:
            continue
        if ledger_index <= 0:
            continue
        if not tx_hash:
            continue
        if not observed_at:
            observed_at = datetime.now(timezone.utc).isoformat()
            limitations.append("observed_at_missing_generated_by_parser")
        if not validated:
            limitations.append("not_validated_do_not_treat_as_final")
        if not metadata_present:
            limitations.append("metadata_missing_signal_is_low_confidence")

        event_id = str(_first_present(row, "event_id", "id") or "").strip()
        if not event_id:
            event_id = _stable_event_id(event_type, issuer, currency_code, ledger_index, tx_hash)

        events.append(
            RawDiscoveryEvent(
                event_id=event_id,
                event_type=event_type,
                issuer=issuer,
                currency_code=currency_code,
                ledger_index=ledger_index,
                tx_hash=tx_hash,
                validated=validated,
                metadata_present=metadata_present,
                observed_at=observed_at,
                limitations=limitations,
            )
        )

    events.sort(key=lambda item: (item.ledger_index, item.tx_hash, item.event_id))
    return events
