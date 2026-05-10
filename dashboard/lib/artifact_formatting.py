from __future__ import annotations

from typing import Any


def normalize_display_value(value: Any) -> str:
    if value is None:
        return "Unavailable"
    if isinstance(value, str):
        return value if value.strip() else "Unavailable"
    if isinstance(value, (int, float)):
        return str(value)
    return "Unavailable"


def safe_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def is_found(value: Any) -> bool:
    return value is not None
