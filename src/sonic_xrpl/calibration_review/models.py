from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

ReadinessStatus = Literal[
    "NOT_READY",
    "NEEDS_MORE_EVIDENCE",
    "READY_FOR_HUMAN_REVIEW",
    "REVIEW_WITH_CAUTION",
]
ThresholdTarget = Literal[
    "signal_score_threshold",
    "risk_score_threshold",
    "watch_threshold",
    "avoid_threshold",
    "evidence_quality_threshold",
    "unknown_penalty",
    "synthetic_penalty",
]
RecommendationDirection = Literal[
    "KEEP",
    "REVIEW_INCREASE",
    "REVIEW_DECREASE",
    "INSUFFICIENT_EVIDENCE",
]


@dataclass(frozen=True)
class CalibrationEvidenceSnapshot:
    snapshot_id: str
    created_at: str
    source_files: tuple[str, ...]
    signal_count: int
    review_count: int
    paper_decision_count: int
    paper_intent_count: int
    attributed_outcome_count: int
    corpus_case_count: int
    source_backed_case_count: int
    synthetic_case_count: int
    missing_observation_count: int
    invalid_observation_count: int
    quality_summary: dict[str, Any]
    limitations: tuple[str, ...] = field(default_factory=tuple)
    signal_type_counts: dict[str, int] = field(default_factory=dict)
    outcome_counts: dict[str, int] = field(default_factory=dict)
    favorable_outcome_counts: dict[str, int] = field(default_factory=dict)
    live_enabled_records: tuple[str, ...] = field(default_factory=tuple)
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    paper_only: bool = True
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class CalibrationReadinessRule:
    rule_id: str
    name: str
    severity: str
    passed: bool
    reason: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CalibrationReadinessResult:
    readiness_id: str
    status: ReadinessStatus
    confidence: float
    rules: tuple[CalibrationReadinessRule, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    evidence_snapshot: CalibrationEvidenceSnapshot
    paper_only: bool = True
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class ThresholdRecommendation:
    recommendation_id: str
    target: ThresholdTarget
    direction: RecommendationDirection
    rationale: str
    evidence_refs: tuple[str, ...]
    confidence: float
    non_mutating: bool = True
    requires_human_review: bool = True
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class CalibrationReviewReport:
    report_id: str
    readiness_result: CalibrationReadinessResult
    recommendations: tuple[ThresholdRecommendation, ...]
    safety_statement: str
    accuracy_statement: str
    generated_files: dict[str, str]
    paper_only: bool = True
    live_execution_allowed: bool = False


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: jsonable(getattr(value, key))
            for key in value.__dataclass_fields__
        }
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value
