from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from sonic_xrpl.outcome_corpus.loader import load_observation_points, resolve_fixture_paths
from sonic_xrpl.outcome_corpus.models import (
    CANONICAL_WINDOWS,
    DETERMINISTIC_GENERATED_AT,
    OutcomeCorpus,
    OutcomeReplayCase,
    PaperObservationPoint,
)
from sonic_xrpl.outcome_corpus.quality import summarize_quality
from sonic_xrpl.signals.evidence import stable_hash, stable_id


def _window_sort_key(point: PaperObservationPoint) -> tuple[int, str, str]:
    try:
        index = CANONICAL_WINDOWS.index(point.window_label)
    except ValueError:
        index = len(CANONICAL_WINDOWS)
    return (index, point.observed_at, point.source)


def _case_limitations(points: list[PaperObservationPoint], windows_missing: tuple[str, ...]) -> tuple[str, ...]:
    limitations: list[str] = []
    for point in points:
        limitations.extend(point.limitations)
        for field in point.missing_fields:
            limitations.append(f"missing_field:{field}")
    if windows_missing:
        limitations.append("missing_windows:" + ",".join(windows_missing))
    return tuple(dict.fromkeys(limitations))


def _metadata_value(points: list[PaperObservationPoint], field: str) -> str | None:
    prefix = field + ":"
    for point in points:
        for limitation in point.limitations:
            if limitation.startswith(prefix):
                return limitation.removeprefix(prefix)
    return None


def build_replay_case(candidate_id: str, points: list[PaperObservationPoint]) -> OutcomeReplayCase:
    ordered = sorted(points, key=_window_sort_key)
    windows_present = tuple(
        window for window in CANONICAL_WINDOWS
        if any(point.window_label == window for point in ordered)
    )
    windows_missing = tuple(window for window in CANONICAL_WINDOWS if window not in windows_present)
    limitations = _case_limitations(ordered, windows_missing)
    evidence_hash = stable_hash(
        [
            {
                "candidate_id": point.candidate_id,
                "observed_at": point.observed_at,
                "window_label": point.window_label,
                "reference_price": point.reference_price,
                "observed_price": point.observed_price,
                "source": point.source,
                "source_url": point.source_url,
                "limitations": point.limitations,
            }
            for point in ordered
        ]
    )
    source_backed = bool(ordered) and all(point.source_backed for point in ordered)
    synthetic = any(point.synthetic for point in ordered)
    return OutcomeReplayCase(
        replay_case_id=stable_id("orc", candidate_id, windows_present, evidence_hash),
        candidate_id=candidate_id,
        signal_id=_metadata_value(ordered, "signal_id"),
        review_id=_metadata_value(ordered, "review_id"),
        paper_intent_id=_metadata_value(ordered, "paper_intent_id"),
        observation_points=tuple(ordered),
        windows_present=windows_present,
        windows_missing=windows_missing,
        limitations=limitations,
        source_backed=source_backed,
        synthetic=synthetic,
        paper_only=True,
        live_execution_allowed=False,
    )


def build_outcome_corpus(
    fixtures: list[str | Path],
    *,
    generated_at: str = DETERMINISTIC_GENERATED_AT,
) -> OutcomeCorpus:
    points = load_observation_points(fixtures)
    grouped: dict[str, list[PaperObservationPoint]] = defaultdict(list)
    for point in points:
        if point.candidate_id:
            grouped[point.candidate_id].append(point)

    cases = [
        build_replay_case(candidate_id, grouped[candidate_id])
        for candidate_id in sorted(grouped)
    ]
    fixture_paths = [str(path) for path in resolve_fixture_paths(fixtures)]
    quality = summarize_quality(cases)
    corpus_id = stable_id(
        "oc",
        tuple(case.replay_case_id for case in cases),
        tuple(fixture_paths),
        generated_at,
    )
    return OutcomeCorpus(
        corpus_id=corpus_id,
        generated_at=generated_at,
        replay_cases=tuple(cases),
        total_cases=len(cases),
        source_backed_cases=sum(1 for case in cases if case.source_backed),
        synthetic_cases=sum(1 for case in cases if case.synthetic),
        limited_cases=sum(1 for case in cases if case.limitations),
        quality_summary=quality,
        paper_only=True,
        live_execution_allowed=False,
    )

