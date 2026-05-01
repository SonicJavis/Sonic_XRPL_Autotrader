from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


DEFAULT_AUDIT_PATH = Path(__file__).with_name("audit_log.jsonl")


def append_audit_record(
    *,
    intent_id: str,
    tx_type: str,
    tx_payload: Mapping[str, object],
    user_confirmed: bool,
    submitted: bool,
    tx_hash: str | None = None,
    path: str | Path = DEFAULT_AUDIT_PATH,
) -> dict[str, object]:
    record = {
        "intent_id": str(intent_id),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "tx_type": str(tx_type),
        "tx_payload": _sorted(dict(tx_payload)),
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


def _sorted(raw: object) -> object:
    if isinstance(raw, dict):
        return {str(key): _sorted(value) for key, value in sorted(raw.items())}
    if isinstance(raw, list):
        return [_sorted(item) for item in raw]
    return raw
