from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from sonic_xrpl.calibration_approval.errors import CalibrationApprovalError
from sonic_xrpl.calibration_approval.models import DETERMINISTIC_CREATED_AT, HumanReviewer


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return tuple()
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    return (str(value),)


def load_review_payload(path: str | Path) -> Mapping[str, Any]:
    fixture_path = Path(path)
    if not fixture_path.is_file():
        raise CalibrationApprovalError(f"Calibration approval fixture not found: {fixture_path}")
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CalibrationApprovalError(f"Calibration approval fixture is not valid JSON: {fixture_path}") from exc
    if not isinstance(payload, Mapping):
        raise CalibrationApprovalError("Calibration approval fixture must be a JSON object")
    return payload


def reviewer_from_payload(payload: Mapping[str, Any], source_path: str) -> HumanReviewer:
    raw = payload.get("reviewer", {})
    reviewer = raw if isinstance(raw, Mapping) else {}
    return HumanReviewer(
        reviewer_id=str(reviewer.get("reviewer_id") or payload.get("reviewer_id") or ""),
        display_name=str(reviewer.get("display_name") or ""),
        role=str(reviewer.get("role") or ""),
        review_source=str(payload.get("review_source") or reviewer.get("review_source") or source_path),
        reviewed_at=str(payload.get("reviewed_at") or reviewer.get("reviewed_at") or DETERMINISTIC_CREATED_AT),
        provenance=tuple(dict.fromkeys((*_as_tuple(payload.get("provenance")), source_path))),
        limitations=_as_tuple(payload.get("limitations")),
    )


def review_items(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    items = payload.get("reviews", [])
    if items in (None, ""):
        return tuple()
    if not isinstance(items, list):
        raise CalibrationApprovalError("reviews must be an array")
    return tuple(item for item in items if isinstance(item, Mapping))
