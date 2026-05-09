from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from sonic_xrpl.calibration_review.errors import CalibrationReviewFixtureError
from sonic_xrpl.calibration_review.models import CalibrationEvidenceSnapshot, DETERMINISTIC_CREATED_AT
from sonic_xrpl.signals.evidence import stable_id


SIGNAL_TYPES: tuple[str, ...] = (
    "BUY_CANDIDATE",
    "WATCH",
    "AVOID",
    "INSUFFICIENT_EVIDENCE",
)


def _as_list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise CalibrationReviewFixtureError("Calibration review fixture fields must be arrays")
    return value


def _as_tuple_of_text(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in _as_list(value))


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _count_by(items: list[Any], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in items:
        if isinstance(item, Mapping):
            counts[str(item.get(key) or "UNKNOWN")] += 1
    return dict(sorted(counts.items()))


def _favorable_counts(attributions: list[Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in attributions:
        if not isinstance(item, Mapping):
            continue
        label = str(item.get("outcome_label") or item.get("outcome") or "").upper()
        signal_type = str(item.get("signal_type") or "UNKNOWN")
        if label == "WIN":
            counts[signal_type] += 1
    return dict(sorted(counts.items()))


def _live_enabled_records(payload: Mapping[str, Any]) -> tuple[str, ...]:
    records: list[str] = []
    groups = ("signals", "reviews", "paper_decisions", "paper_intents", "attributions")
    for group in groups:
        for index, item in enumerate(_as_list(payload.get(group))):
            if isinstance(item, Mapping) and _bool(item.get("live_execution_allowed"), False):
                records.append(f"{group}[{index}]")

    corpus = payload.get("corpus")
    if isinstance(corpus, Mapping):
        if _bool(corpus.get("live_execution_allowed"), False):
            records.append("corpus")
        for index, case in enumerate(_as_list(corpus.get("replay_cases"))):
            if isinstance(case, Mapping) and _bool(case.get("live_execution_allowed"), False):
                records.append(f"corpus.replay_cases[{index}]")
    return tuple(records)


def _invalid_observation_count(corpus: Mapping[str, Any]) -> int:
    count = 0
    limitation_counts = corpus.get("quality_summary", {}).get("limitation_counts", {})
    if isinstance(limitation_counts, Mapping):
        for key, value in limitation_counts.items():
            if str(key).startswith("invalid_numeric_field:"):
                count += int(value)
    for case in _as_list(corpus.get("replay_cases")):
        if not isinstance(case, Mapping):
            continue
        limitations = _as_tuple_of_text(case.get("limitations"))
        if any(item.startswith("invalid_numeric_field:") for item in limitations):
            count += 1
        for point in _as_list(case.get("observation_points")):
            if isinstance(point, Mapping):
                point_limitations = _as_tuple_of_text(point.get("limitations"))
                if any(item.startswith("invalid_numeric_field:") for item in point_limitations):
                    count += 1
    return count


def _missing_observation_count(payload: Mapping[str, Any], corpus: Mapping[str, Any]) -> int:
    missing = int(corpus.get("quality_summary", {}).get("missing_observation_cases", 0) or 0)
    for attribution in _as_list(payload.get("attributions")):
        if isinstance(attribution, Mapping) and str(attribution.get("outcome_label") or "").upper() == "NO_OBSERVATION":
            missing += 1
    return missing


def _snapshot_from_phase52_corpus(payload: Mapping[str, Any], source_path: Path) -> CalibrationEvidenceSnapshot:
    corpus = payload
    source_files = (str(source_path),)
    source_backed = int(corpus.get("source_backed_cases", 0) or 0)
    synthetic = int(corpus.get("synthetic_cases", 0) or 0)
    total = int(corpus.get("total_cases", 0) or 0)
    quality = dict(corpus.get("quality_summary", {}))
    limitations = []
    for case in _as_list(corpus.get("replay_cases")):
        if isinstance(case, Mapping):
            limitations.extend(_as_tuple_of_text(case.get("limitations")))
    snapshot_id = stable_id("crs", source_files, total, source_backed, synthetic, quality, tuple(sorted(limitations)))
    return CalibrationEvidenceSnapshot(
        snapshot_id=snapshot_id,
        created_at=DETERMINISTIC_CREATED_AT,
        source_files=source_files,
        signal_count=0,
        review_count=0,
        paper_decision_count=0,
        paper_intent_count=0,
        attributed_outcome_count=0,
        corpus_case_count=total,
        source_backed_case_count=source_backed,
        synthetic_case_count=synthetic,
        missing_observation_count=_missing_observation_count({}, corpus),
        invalid_observation_count=_invalid_observation_count(corpus),
        quality_summary=quality,
        limitations=tuple(dict.fromkeys(limitations)),
        signal_type_counts={signal_type: 0 for signal_type in SIGNAL_TYPES},
        outcome_counts={},
        favorable_outcome_counts={},
        live_enabled_records=tuple(),
        provenance_refs=source_files,
    )


def _snapshot_from_calibration_payload(payload: Mapping[str, Any], source_path: Path) -> CalibrationEvidenceSnapshot:
    signals = _as_list(payload.get("signals"))
    reviews = _as_list(payload.get("reviews"))
    decisions = _as_list(payload.get("paper_decisions"))
    intents = _as_list(payload.get("paper_intents"))
    attributions = _as_list(payload.get("attributions"))
    corpus = payload.get("corpus") if isinstance(payload.get("corpus"), Mapping) else {}
    source_files = tuple(sorted(set((str(source_path), *_as_tuple_of_text(payload.get("source_files"))))))
    signal_type_counts = {signal_type: 0 for signal_type in SIGNAL_TYPES}
    signal_type_counts.update(_count_by(signals, "signal_type"))
    outcome_counts = _count_by(attributions, "outcome_label")
    source_backed = int(corpus.get("source_backed_cases", payload.get("source_backed_case_count", 0)) or 0)
    synthetic = int(corpus.get("synthetic_cases", payload.get("synthetic_case_count", 0)) or 0)
    total_cases = int(corpus.get("total_cases", payload.get("corpus_case_count", 0)) or 0)
    quality = dict(corpus.get("quality_summary", payload.get("quality_summary", {})))
    limitations = tuple(dict.fromkeys((
        *_as_tuple_of_text(payload.get("limitations")),
        *[
            limitation
            for case in _as_list(corpus.get("replay_cases"))
            if isinstance(case, Mapping)
            for limitation in _as_tuple_of_text(case.get("limitations"))
        ],
    )))
    live_enabled = _live_enabled_records(payload)
    provenance = tuple(dict.fromkeys((*source_files, *_as_tuple_of_text(payload.get("provenance_refs")))))
    snapshot_id = stable_id(
        "crs",
        source_files,
        len(signals),
        len(reviews),
        len(decisions),
        len(intents),
        len(attributions),
        total_cases,
        source_backed,
        synthetic,
        signal_type_counts,
        outcome_counts,
        limitations,
        live_enabled,
    )
    return CalibrationEvidenceSnapshot(
        snapshot_id=snapshot_id,
        created_at=str(payload.get("created_at") or DETERMINISTIC_CREATED_AT),
        source_files=source_files,
        signal_count=len(signals),
        review_count=len(reviews),
        paper_decision_count=len(decisions),
        paper_intent_count=len(intents),
        attributed_outcome_count=len(attributions),
        corpus_case_count=total_cases,
        source_backed_case_count=source_backed,
        synthetic_case_count=synthetic,
        missing_observation_count=_missing_observation_count(payload, corpus),
        invalid_observation_count=int(payload.get("invalid_observation_count") or 0) + _invalid_observation_count(corpus),
        quality_summary=quality,
        limitations=limitations,
        signal_type_counts=dict(sorted(signal_type_counts.items())),
        outcome_counts=outcome_counts,
        favorable_outcome_counts=_favorable_counts(attributions),
        live_enabled_records=live_enabled,
        provenance_refs=provenance,
        paper_only=_bool(payload.get("paper_only"), True),
        live_execution_allowed=_bool(payload.get("live_execution_allowed"), False),
    )


def load_evidence_snapshot(path: str | Path) -> CalibrationEvidenceSnapshot:
    fixture_path = Path(path)
    if not fixture_path.is_file():
        raise CalibrationReviewFixtureError(f"Calibration review fixture not found: {fixture_path}")
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CalibrationReviewFixtureError(f"Calibration review fixture is not valid JSON: {fixture_path}") from exc
    if not isinstance(payload, Mapping):
        raise CalibrationReviewFixtureError("Calibration review fixture must be a JSON object")
    if "replay_cases" in payload and "corpus_id" in payload:
        return _snapshot_from_phase52_corpus(payload, fixture_path)
    return _snapshot_from_calibration_payload(payload, fixture_path)
