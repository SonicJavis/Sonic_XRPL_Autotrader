from __future__ import annotations

from typing import Any, Mapping

from sonic_xrpl.calibration_approval.change_request import build_change_request
from sonic_xrpl.calibration_approval.models import (
    CalibrationApprovalRecord,
    CalibrationChangeRequest,
    HumanReviewer,
)
from sonic_xrpl.calibration_proposal.models import CalibrationProposal, CalibrationProposalPack
from sonic_xrpl.signals.evidence import stable_hash, stable_id


VALID_DECISIONS = {
    "APPROVED_FOR_CHANGE_REQUEST",
    "REJECTED",
    "DEFERRED",
    "NEEDS_REVISION",
    "BLOCKED",
    "INVALID_REVIEW",
}
SUPPORTED_DIRECTIONS = {"REVIEW_INCREASE", "REVIEW_DECREASE"}
SAFETY_SUMMARY = (
    "Phase 55 approval ledger is offline, paper-only, and non-mutating. "
    "No calibration changes are applied. Live execution remains blocked."
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _decision(review: Mapping[str, Any]) -> str:
    raw = _text(review.get("decision")).upper()
    return raw if raw in VALID_DECISIONS else "INVALID_REVIEW"


def _proposal_by_id(pack: CalibrationProposalPack, proposal_id: str) -> CalibrationProposal | None:
    for proposal in pack.proposals:
        if proposal.proposal_id == proposal_id:
            return proposal
    return None


def _blocked_proposal_ids(pack: CalibrationProposalPack) -> set[str]:
    return {item.recommendation_id for item in pack.blocked_recommendations}


def _review_limitations(
    pack: CalibrationProposalPack,
    proposal: CalibrationProposal | None,
    reviewer: HumanReviewer,
    review: Mapping[str, Any],
    decision: str,
) -> tuple[str, ...]:
    limitations: list[str] = []
    if not reviewer.reviewer_id:
        limitations.append("reviewer_id_missing")
    if not _text(review.get("decision_reason")):
        limitations.append("decision_reason_missing")
    if decision == "INVALID_REVIEW":
        limitations.append("invalid_review_decision")
    if not pack.paper_only:
        limitations.append("proposal_pack_not_paper_only")
    if pack.auto_apply_allowed:
        limitations.append("proposal_pack_auto_apply_not_blocked")
    if pack.live_execution_allowed:
        limitations.append("proposal_pack_live_execution_not_blocked")
    if proposal is None:
        limitations.append("proposal_not_found_or_blocked")
    else:
        if proposal.auto_apply_allowed:
            limitations.append("proposal_auto_apply_not_blocked")
        if proposal.live_execution_allowed:
            limitations.append("proposal_live_execution_not_blocked")
        if not proposal.human_review_required:
            limitations.append("proposal_human_review_not_required")
        if proposal.direction not in SUPPORTED_DIRECTIONS:
            limitations.append("unsupported_proposal_direction")
        before = _number(proposal.current_value)
        after = _number(proposal.proposed_value)
        delta = _number(proposal.exact_delta)
        if before is None or after is None or delta is None:
            limitations.append("invalid_numeric_proposal")
        else:
            lower, upper = proposal.parameter_ref.allowed_range
            if not (float(lower) <= after <= float(upper)):
                limitations.append("proposal_after_value_out_of_range")
            if round(after - before, 2) != round(delta, 2):
                limitations.append("proposal_delta_mismatch")
        limitations.extend(proposal.limitations)
    limitations.extend(pack.limitations)
    limitations.extend(reviewer.limitations)
    return tuple(dict.fromkeys(str(item) for item in limitations if item))


def _record(
    pack: CalibrationProposalPack,
    proposal: CalibrationProposal | None,
    proposal_id: str,
    reviewer: HumanReviewer,
    review: Mapping[str, Any],
    decision: str,
    limitations: tuple[str, ...],
) -> CalibrationApprovalRecord:
    before = proposal.current_value if proposal else None
    after = proposal.proposed_value if proposal else None
    delta = proposal.exact_delta if proposal else None
    signal_class = proposal.parameter_ref.name if proposal else _text(review.get("proposal_signal_class") or "UNKNOWN")
    direction = proposal.direction if proposal else _text(review.get("proposal_direction") or "UNKNOWN")
    decision_reason = _text(review.get("decision_reason"))
    notes = _text(review.get("reviewer_notes"))
    evidence = proposal.evidence_summary if proposal else _text(review.get("evidence_summary") or "Proposal evidence unavailable.")
    content = {
        "pack": pack.pack_id,
        "proposal": proposal_id,
        "reviewer": reviewer.reviewer_id,
        "decision": decision,
        "reason": decision_reason,
        "before": before,
        "after": after,
        "delta": delta,
        "limitations": limitations,
    }
    content_hash = stable_hash(content)
    record_id = stable_id("car", content_hash)
    safety_flags = {
        "paper_only": True,
        "offline_only": True,
        "live_execution_allowed": False,
        "auto_apply_allowed": False,
        "runtime_mutation_allowed": False,
        "requires_human_review": True,
    }
    return CalibrationApprovalRecord(
        approval_record_id=record_id,
        proposal_pack_id=pack.pack_id,
        proposal_id=proposal_id,
        proposal_signal_class=signal_class,
        proposal_direction=direction,
        proposal_before_value=before,
        proposal_after_value=after,
        proposal_delta=delta,
        reviewer=reviewer,
        decision=decision,  # type: ignore[arg-type]
        decision_reason=decision_reason,
        reviewer_notes=notes,
        evidence_summary=evidence,
        limitation_summary=limitations,
        safety_flags=safety_flags,
        deterministic_hash=content_hash,
        content_hash=content_hash,
        created_at=reviewer.reviewed_at,
        paper_only=True,
        offline_only=True,
        live_execution_allowed=False,
        auto_apply_allowed=False,
        runtime_mutation_allowed=False,
        requires_human_review=True,
    )


def evaluate_review(
    pack: CalibrationProposalPack,
    reviewer: HumanReviewer,
    review: Mapping[str, Any],
) -> tuple[CalibrationApprovalRecord, CalibrationChangeRequest | None]:
    proposal_id = _text(review.get("proposal_id"))
    proposal = _proposal_by_id(pack, proposal_id)
    if proposal_id in _blocked_proposal_ids(pack):
        proposal = None
    decision = _decision(review)
    limitations = _review_limitations(pack, proposal, reviewer, review, decision)
    if limitations and decision == "APPROVED_FOR_CHANGE_REQUEST":
        decision = "BLOCKED"
    record = _record(pack, proposal, proposal_id, reviewer, review, decision, limitations)
    if (
        record.decision == "APPROVED_FOR_CHANGE_REQUEST"
        and proposal is not None
        and not record.limitation_summary
    ):
        return record, build_change_request(record)
    return record, None
