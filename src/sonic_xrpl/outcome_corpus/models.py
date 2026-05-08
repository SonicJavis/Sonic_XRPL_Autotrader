from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CANONICAL_WINDOWS: tuple[str, ...] = ("5m", "15m", "1h", "4h", "24h")
WINDOW_SECONDS: dict[str, int] = {
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "24h": 86400,
}
DETERMINISTIC_GENERATED_AT = "1970-01-01T00:00:00+00:00"


@dataclass(frozen=True)
class PaperObservationWindow:
    window_id: str
    label: str
    duration_seconds: int
    source_backed: bool
    paper_only: bool = True


@dataclass(frozen=True)
class PaperObservationPoint:
    candidate_id: str
    observed_at: str
    window_label: str
    reference_price: float | str | None
    observed_price: float | str | None
    observed_return_pct: float | str | None
    liquidity_state: str | None
    volume_state: str | None
    source: str
    source_url: str | None
    source_backed: bool
    synthetic: bool
    limitations: tuple[str, ...] = field(default_factory=tuple)
    missing_fields: tuple[str, ...] = field(default_factory=tuple)
    paper_only: bool = True


@dataclass(frozen=True)
class OutcomeReplayCase:
    replay_case_id: str
    candidate_id: str
    signal_id: str | None
    review_id: str | None
    paper_intent_id: str | None
    observation_points: tuple[PaperObservationPoint, ...]
    windows_present: tuple[str, ...]
    windows_missing: tuple[str, ...]
    limitations: tuple[str, ...] = field(default_factory=tuple)
    source_backed: bool = False
    synthetic: bool = False
    paper_only: bool = True
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class CorpusQualitySummary:
    total_cases: int
    complete_cases: int
    partial_cases: int
    missing_observation_cases: int
    source_backed_cases: int
    synthetic_cases: int
    average_windows_present: float
    limitation_counts: dict[str, int]
    quality_grade: str
    recommendation: str


@dataclass(frozen=True)
class OutcomeCorpus:
    corpus_id: str
    generated_at: str
    replay_cases: tuple[OutcomeReplayCase, ...]
    total_cases: int
    source_backed_cases: int
    synthetic_cases: int
    limited_cases: int
    quality_summary: CorpusQualitySummary
    paper_only: bool = True
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class OutcomeCorpusReport:
    corpus: OutcomeCorpus
    generated_files: dict[str, str]
    safety_statement: str
    limitations: tuple[str, ...]
    next_recommended_action: str


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: jsonable(getattr(value, key))
            for key in value.__dataclass_fields__
        }
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value

