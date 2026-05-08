from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from sonic_xrpl.outcome_corpus.errors import OutcomeCorpusFixtureError
from sonic_xrpl.outcome_corpus.models import PaperObservationPoint
from sonic_xrpl.outcome_corpus.validation import (
    is_valid_numeric_value,
    missing_fields_for_row,
    normalize_window_label,
    validation_limitations,
)


def resolve_fixture_paths(fixtures: Iterable[str | Path]) -> list[Path]:
    paths: list[Path] = []
    for item in fixtures:
        path = Path(item)
        if path.is_dir():
            paths.extend(sorted(child for child in path.glob("*.json") if child.is_file()))
        elif path.is_file():
            paths.append(path)
        else:
            raise OutcomeCorpusFixtureError(f"Outcome corpus fixture not found: {path}")
    return sorted(dict.fromkeys(paths))


def _rows_from_payload(payload: Any) -> list[Mapping[str, Any]]:
    rows = payload.get("observations", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise OutcomeCorpusFixtureError("Outcome corpus fixture must be a list or contain observations")
    result: list[Mapping[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise OutcomeCorpusFixtureError("Outcome corpus observation rows must be objects")
        result.append(row)
    return result


def _optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _safe_number(value: Any) -> float | str | None:
    if value in (None, ""):
        return None
    if not is_valid_numeric_value(value):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = str(value).strip()
    return float(text)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "source_backed", "synthetic"}
    return bool(value)


def _list_of_text(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return tuple()
    if not isinstance(value, list):
        raise OutcomeCorpusFixtureError("limitations and missing_fields must be lists")
    return tuple(str(item) for item in value)


def point_from_row(row: Mapping[str, Any], source_path: Path) -> PaperObservationPoint:
    missing = tuple(dict.fromkeys((*_list_of_text(row.get("missing_fields")), *missing_fields_for_row(row))))
    limitations = tuple(
        dict.fromkeys(
            (
                *_list_of_text(row.get("limitations")),
                *validation_limitations(row, missing),
            )
        )
    )
    source = str(row.get("source") or row.get("source_fixture") or row.get("source_identifier") or "").strip()
    synthetic = _as_bool(row.get("synthetic", False))
    source_backed = _as_bool(row.get("source_backed", False)) and not synthetic

    if source_backed and ("source" in missing or "observed_at" in missing):
        source_backed = False

    return PaperObservationPoint(
        candidate_id=str(row.get("candidate_id") or "").strip(),
        observed_at=str(row.get("observed_at") or "").strip(),
        window_label=normalize_window_label(row.get("window_label", row.get("window"))),
        reference_price=_safe_number(row.get("reference_price", row.get("entry_price_xrp"))),
        observed_price=_safe_number(row.get("observed_price", row.get("exit_price_xrp"))),
        observed_return_pct=_safe_number(row.get("observed_return_pct")),
        liquidity_state=_optional_text(row.get("liquidity_state")),
        volume_state=_optional_text(row.get("volume_state")),
        source=source or str(source_path),
        source_url=_optional_text(row.get("source_url")),
        source_backed=source_backed,
        synthetic=synthetic,
        limitations=limitations,
        missing_fields=missing,
        paper_only=True,
    )


def load_observation_points(fixtures: Iterable[str | Path]) -> list[PaperObservationPoint]:
    points: list[PaperObservationPoint] = []
    for path in resolve_fixture_paths(fixtures):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise OutcomeCorpusFixtureError(f"Outcome corpus fixture is not valid JSON: {path}") from exc
        for row in _rows_from_payload(payload):
            points.append(point_from_row(row, path))
    points.sort(key=lambda item: (item.candidate_id, item.window_label, item.observed_at, item.source))
    return points
