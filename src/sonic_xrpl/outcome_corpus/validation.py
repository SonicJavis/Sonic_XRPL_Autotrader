from __future__ import annotations

import math
from typing import Any, Mapping

from sonic_xrpl.outcome_corpus.models import CANONICAL_WINDOWS


REQUIRED_POINT_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "observed_at",
    "window_label",
    "reference_price",
    "observed_price",
    "source",
)


def normalize_window_label(value: Any) -> str:
    label = str(value or "").strip()
    return label


def _is_missing_value(value: Any) -> bool:
    return value in (None, "")


def _numeric_value(row: Mapping[str, Any], field: str) -> Any:
    aliases = {
        "reference_price": ("reference_price", "entry_price_xrp"),
        "observed_price": ("observed_price", "exit_price_xrp"),
        "observed_return_pct": ("observed_return_pct",),
    }
    for key in aliases[field]:
        if not _is_missing_value(row.get(key)):
            return row.get(key)
    return None


def is_valid_numeric_value(value: Any) -> bool:
    if _is_missing_value(value) or isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    try:
        return math.isfinite(float(str(value).strip()))
    except (TypeError, ValueError):
        return False


def invalid_numeric_fields(row: Mapping[str, Any]) -> tuple[str, ...]:
    invalid: list[str] = []
    for field in ("reference_price", "observed_price", "observed_return_pct"):
        value = _numeric_value(row, field)
        if not _is_missing_value(value) and not is_valid_numeric_value(value):
            invalid.append(field)
    return tuple(invalid)


def missing_fields_for_row(row: Mapping[str, Any]) -> tuple[str, ...]:
    missing: list[str] = []
    aliases = {
        "window_label": ("window_label", "window"),
        "reference_price": ("reference_price", "entry_price_xrp"),
        "observed_price": ("observed_price", "exit_price_xrp"),
        "source": ("source", "source_fixture", "source_identifier"),
    }
    for field in REQUIRED_POINT_FIELDS:
        keys = aliases.get(field, (field,))
        if all(row.get(key) in (None, "") for key in keys):
            missing.append(field)
    for field in invalid_numeric_fields(row):
        if field in REQUIRED_POINT_FIELDS and field not in missing:
            missing.append(field)
    return tuple(missing)


def validation_limitations(row: Mapping[str, Any], missing_fields: tuple[str, ...]) -> tuple[str, ...]:
    limitations: list[str] = []
    window = normalize_window_label(row.get("window_label", row.get("window")))
    if missing_fields:
        limitations.append("missing_fields:" + ",".join(missing_fields))
    if window and window not in CANONICAL_WINDOWS:
        limitations.append("non_canonical_window:" + window)
    for field in invalid_numeric_fields(row):
        limitations.append("invalid_numeric_field:" + field)
    if not row.get("observed_at"):
        limitations.append("observed_at_missing")
    if not row.get("source") and not row.get("source_fixture") and not row.get("source_identifier"):
        limitations.append("source_missing")
    if row.get("source_backed") is True and row.get("synthetic") is True:
        limitations.append("synthetic_cannot_be_source_backed")
    return tuple(limitations)
