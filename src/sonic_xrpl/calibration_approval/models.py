from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
PHASE = "55"

CalibrationReviewDecision = Literal[
    "APPROVED_FOR_CHANGE_REQUEST",
    "REJECTED",
    "DEFERRED",
    "NEEDS_REVISION",
    "BLOCKED",
    "INVALID_REVIEW",
]
ChangeRequestStatus = Literal["REQUESTED", "BLOCKED", "INVALID"]


@dataclass(frozen=True)
class HumanReviewer:
    reviewer_id: str
    display_name: str = ""
    role: str = ""
    review_source: str = ""
    reviewed_at: str = DETERMINISTIC_CREATED_AT
    provenance: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CalibrationApprovalRecord:
    approval_record_id: str
    proposal_pack_id: str
    proposal_id: str
    proposal_signal_class: str
    proposal_direction: str
    proposal_before_value: float | None
    proposal_after_value: float | None
    proposal_delta: float | None
    reviewer: HumanReviewer
    decision: CalibrationReviewDecision
    decision_reason: str
    reviewer_notes: str
    evidence_summary: str
    limitation_summary: tuple[str, ...]
    safety_flags: dict[str, bool]
    deterministic_hash: str
    content_hash: str
    created_at: str = DETERMINISTIC_CREATED_AT
    paper_only: bool = True
    offline_only: bool = True
    live_execution_allowed: bool = False
    auto_apply_allowed: bool = False
    runtime_mutation_allowed: bool = False
    requires_human_review: bool = True


@dataclass(frozen=True)
class CalibrationChangeRequest:
    change_request_id: str
    approval_record_id: str
    proposal_pack_id: str
    proposal_id: str
    requested_change: str
    before_value: float
    after_value: float
    delta: float
    rationale: str
    required_follow_up: tuple[str, ...]
    status: ChangeRequestStatus = "REQUESTED"
    change_request_only: bool = True
    apply_allowed: bool = False
    live_execution_allowed: bool = False
    runtime_mutation_allowed: bool = False
    paper_only: bool = True
    offline_only: bool = True


@dataclass(frozen=True)
class ApprovalLedger:
    ledger_id: str
    records: tuple[CalibrationApprovalRecord, ...]
    change_requests: tuple[CalibrationChangeRequest, ...]
    counts_by_decision: dict[str, int]
    counts_by_change_request_status: dict[str, int]
    blocked_count: int
    approved_count: int
    invalid_count: int
    generated_at: str
    safety_summary: str
    limitation_summary: tuple[str, ...]


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
