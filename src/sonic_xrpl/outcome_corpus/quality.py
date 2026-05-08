from __future__ import annotations

from collections import Counter

from sonic_xrpl.outcome_corpus.models import CANONICAL_WINDOWS, CorpusQualitySummary, OutcomeReplayCase


def limitation_counts(cases: list[OutcomeReplayCase]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for case in cases:
        for limitation in case.limitations:
            counter[limitation] += 1
    return dict(sorted(counter.items()))


def _grade(
    *,
    total_cases: int,
    complete_cases: int,
    source_backed_cases: int,
    synthetic_cases: int,
    average_windows_present: float,
    limitations: dict[str, int],
) -> str:
    if total_cases == 0:
        return "INSUFFICIENT"
    has_critical = any(
        key.startswith("observed_at_missing")
        or key.startswith("source_missing")
        or key.startswith("missing_field:")
        or key.startswith("missing_fields:")
        or key.startswith("invalid_numeric_field:")
        or key.startswith("reference_price_missing")
        or key.startswith("observed_price_missing")
        for key in limitations
    )
    if synthetic_cases:
        return "D" if average_windows_present < 3 else "C"
    if complete_cases == total_cases and source_backed_cases == total_cases and not has_critical:
        return "A"
    if source_backed_cases == total_cases and average_windows_present >= 4 and not has_critical:
        return "B"
    if average_windows_present >= 2:
        return "C"
    return "D"


def _has_critical_limitations(limitations: tuple[str, ...]) -> bool:
    return any(
        key.startswith("observed_at_missing")
        or key.startswith("source_missing")
        or key.startswith("missing_field:")
        or key.startswith("missing_fields:")
        or key.startswith("invalid_numeric_field:")
        or key.startswith("reference_price_missing")
        or key.startswith("observed_price_missing")
        for key in limitations
    )


def _recommendation(grade: str) -> str:
    if grade == "A":
        return "Use corpus for Phase 53 calibration review planning only; do not change strategy settings automatically."
    if grade == "B":
        return "Add remaining observation windows before calibration review."
    if grade == "C":
        return "Expand source-backed observations and provenance before using this corpus for calibration review."
    if grade == "D":
        return "Treat corpus as limited training material; collect better source-backed paper observations."
    return "Collect usable paper observation fixtures before running calibration review."


def summarize_quality(cases: list[OutcomeReplayCase]) -> CorpusQualitySummary:
    total = len(cases)
    complete = sum(
        1
        for case in cases
        if not case.windows_missing
        and case.source_backed
        and not case.synthetic
        and not _has_critical_limitations(case.limitations)
    )
    missing_observation_cases = sum(1 for case in cases if not case.observation_points)
    partial = total - complete - missing_observation_cases
    source_backed = sum(1 for case in cases if case.source_backed)
    synthetic = sum(1 for case in cases if case.synthetic)
    avg_windows = round(sum(len(case.windows_present) for case in cases) / total, 2) if total else 0.0
    counts = limitation_counts(cases)
    grade = _grade(
        total_cases=total,
        complete_cases=complete,
        source_backed_cases=source_backed,
        synthetic_cases=synthetic,
        average_windows_present=avg_windows,
        limitations=counts,
    )
    return CorpusQualitySummary(
        total_cases=total,
        complete_cases=complete,
        partial_cases=partial,
        missing_observation_cases=missing_observation_cases,
        source_backed_cases=source_backed,
        synthetic_cases=synthetic,
        average_windows_present=avg_windows,
        limitation_counts=counts,
        quality_grade=grade,
        recommendation=_recommendation(grade),
    )


def canonical_window_coverage(case: OutcomeReplayCase) -> dict[str, bool]:
    return {window: window in case.windows_present for window in CANONICAL_WINDOWS}
