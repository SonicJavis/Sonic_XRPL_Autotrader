from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


DEFAULT_AUDIT_PATH = Path(__file__).with_name("audit_log.jsonl")
DEFAULT_LIFECYCLE_AUDIT_PATH = Path(__file__).with_name("lifecycle_audit_log.jsonl")


def append_audit_record(
    *,
    intent_id: str,
    tx_type: str,
    tx_payload: Mapping[str, object],
    user_confirmed: bool,
    submitted: bool,
    tx_hash: str | None = None,
    execution_type: str | None = None,
    expected_fill_range: Mapping[str, object] | None = None,
    liquidity_source: str | None = None,
    decay_status: str | None = None,
    user_acknowledged_risk: bool = False,
    path: str | Path = DEFAULT_AUDIT_PATH,
) -> dict[str, object]:
    record = {
        "decay_status": str(decay_status or "unknown"),
        "execution_type": str(execution_type or tx_type),
        "expected_fill_range": _sorted(dict(expected_fill_range or {})),
        "intent_id": str(intent_id),
        "liquidity_source": str(liquidity_source or "unknown"),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "tx_type": str(tx_type),
        "tx_payload": _sorted(dict(tx_payload)),
        "user_acknowledged_risk": bool(user_acknowledged_risk),
        "user_confirmed": bool(user_confirmed),
        "submitted": bool(submitted),
    }
    if tx_hash:
        record["tx_hash"] = str(tx_hash)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return record


def read_audit_records(path: str | Path = DEFAULT_AUDIT_PATH) -> list[dict[str, object]]:
    target = Path(path)
    if not target.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        if isinstance(raw, dict):
            rows.append(raw)
    return rows


def append_lifecycle_audit_record(
    *,
    event_type: str,
    session_id: str,
    intent_id: str,
    tx_hash: str | None = None,
    engine_result: str | None = None,
    path: str | Path = DEFAULT_LIFECYCLE_AUDIT_PATH,
) -> dict[str, object]:
    record = {
        "engine_result": str(engine_result) if engine_result else None,
        "event_type": str(event_type),
        "intent_id": str(intent_id),
        "session_id": str(session_id),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "tx_hash": str(tx_hash) if tx_hash else None,
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    return record


def _sorted(raw: object) -> object:
    if isinstance(raw, dict):
        return {str(key): _sorted(value) for key, value in sorted(raw.items())}
    if isinstance(raw, list):
        return [_sorted(item) for item in raw]
    return raw
