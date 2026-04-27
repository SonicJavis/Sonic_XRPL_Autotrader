from __future__ import annotations

from typing import Any


def normalize_amount(value: Any) -> float:
    """Normalize XRPL amount values.

    - str/int digit values are treated as XRP drops and converted to XRP
    - dict values are treated as IOU amount objects and parsed from "value"
    - decimal-like strings are treated as direct numeric values
    """
    if isinstance(value, dict):
        return float(value.get("value", 0.0))

    if isinstance(value, int):
        return value / 1_000_000.0

    if isinstance(value, str):
        raw = value.strip()
        if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
            return int(raw) / 1_000_000.0
        return float(raw)

    return float(value)
