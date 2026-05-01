from __future__ import annotations

from typing import Callable, Mapping


def check_tx(tx_hash: str, lookup: Callable[[str], Mapping[str, object]] | None = None) -> dict[str, object]:
    if not str(tx_hash).strip():
        raise ValueError("tx_hash is required")
    if lookup is None:
        return {
            "tx_hash": str(tx_hash),
            "checked": False,
            "reason": "manual_lookup_function_not_provided",
            "is_executable": False,
        }
    result = dict(lookup(str(tx_hash)))
    return {
        "checked": True,
        "engine_result": result.get("engine_result"),
        "engine_result_message": result.get("engine_result_message"),
        "ledger_index": result.get("ledger_index"),
        "tx_hash": str(tx_hash),
        "validated": bool(result.get("validated", False)),
        "is_executable": False,
    }
