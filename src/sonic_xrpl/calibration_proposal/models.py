from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
PHASE = "54"

ProposalDirection = Literal["KEEP", "REVIEW_INCREASE", "REVIEW_DECREASE"]
ProposalStatus = Literal["PROPOSED_FOR_HUMAN_REVIEW"]
ProposalTarget = Literal[
    "signal_score_threshold",
    "risk_score_threshold",
    "watch_threshold",
    "avoid_threshold",
    "evidence_quality_threshold",
    "unknown_penalty",
    "synthetic_penalty",
]


@dataclass(frozen=True)
class CalibrationParameterRef:
    namespace: str
    name: ProposalTarget
    description: str
    current_value: float
    proposed_value: float
    value_type: str
    allowed_range: tuple[float, float]
    unit: str
    source: str


@dataclass(frozen=True)
class CalibrationProposal:
    proposal_id: str
    created_at: str
    phase: str
    source_readiness_id: str
    source_recommendation_id: str
    parameter_ref: CalibrationParameterRef
    direction: ProposalDirection
    exact_delta: float
    current_value: float
    proposed_value: float
    confidence: float
    evidence_summary: str
    supporting_evidence_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    risk_notes: tuple[str, ...]
    rollback_note: str
    human_review_required: bool = True
    auto_apply_allowed: bool = False
    live_execution_allowed: bool = False
    status: ProposalStatus = "PROPOSED_FOR_HUMAN_REVIEW"


@dataclass(frozen=True)
class BlockedCalibrationProposal:
    recommendation_id: str
    reason: str
    missing_evidence: tuple[str, ...]
    limitations: tuple[str, ...]
    required_next_evidence: tuple[str, ...]


@dataclass(frozen=True)
class ReviewChecklistItem:
    item_id: str
    question: str
    required: bool
    status: str
    evidence_reference: str


@dataclass(frozen=True)
class ProposalRiskSummary:
    risk_level: str
    reasons: tuple[str, ...]
    evidence_quality: str
    synthetic_ratio: float
    missing_observation_count: int
    invalid_observation_count: int
    sparse_class_warnings: tuple[str, ...]


@dataclass(frozen=True)
class CalibrationProposalPack:
    pack_id: str
    created_at: str
    phase: str
    input_summary: dict[str, Any]
    proposals: tuple[CalibrationProposal, ...]
    blocked_recommendations: tuple[BlockedCalibrationProposal, ...]
    review_checklist: tuple[ReviewChecklistItem, ...]
    approval_requirements: tuple[str, ...]
    safety_statement: str
    limitations: tuple[str, ...]
    risk_summary: ProposalRiskSummary
    paper_only: bool = True
    auto_apply_allowed: bool = False
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
