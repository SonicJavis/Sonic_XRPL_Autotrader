from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

from sonic_xrpl.calibration_approval.approval_policy import SAFETY_SUMMARY, evaluate_review
from sonic_xrpl.calibration_approval.models import ApprovalLedger, DETERMINISTIC_CREATED_AT
from sonic_xrpl.calibration_approval.review_record import load_review_payload, review_items, reviewer_from_payload
from sonic_xrpl.calibration_proposal import build_calibration_proposal_pack
from sonic_xrpl.calibration_proposal.models import (
    BlockedCalibrationProposal,
    CalibrationParameterRef,
    CalibrationProposal,
    CalibrationProposalPack,
    ProposalRiskSummary,
    ReviewChecklistItem,
)
from sonic_xrpl.signals.evidence import stable_id


def _tuple_text(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if str(item))
    return (str(value),) if str(value) else ()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _float_pair(value: Any, default: tuple[float, float] = (0.0, 1.0)) -> tuple[float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            return (float(value[0]), float(value[1]))
        except (TypeError, ValueError):
            return default
    return default


def _parameter_ref(payload: Mapping[str, Any]) -> CalibrationParameterRef:
    return CalibrationParameterRef(
        namespace=str(payload.get("namespace") or "paper_calibration"),
        name=payload.get("name") or "signal_score_threshold",
        description=str(payload.get("description") or "Loaded from Phase 54 proposal pack."),
        current_value=float(payload.get("current_value") or 0.0),
        proposed_value=float(payload.get("proposed_value") or 0.0),
        value_type=str(payload.get("value_type") or "ratio"),
        allowed_range=_float_pair(payload.get("allowed_range")),
        unit=str(payload.get("unit") or "ratio"),
        source=str(payload.get("source") or "phase54_proposal_pack"),
    )


def _proposal(payload: Mapping[str, Any]) -> CalibrationProposal:
    return CalibrationProposal(
        proposal_id=str(payload.get("proposal_id") or ""),
        created_at=str(payload.get("created_at") or DETERMINISTIC_CREATED_AT),
        phase=str(payload.get("phase") or "54"),
        source_readiness_id=str(payload.get("source_readiness_id") or ""),
        source_recommendation_id=str(payload.get("source_recommendation_id") or ""),
        parameter_ref=_parameter_ref(_mapping(payload.get("parameter_ref"))),
        direction=payload.get("direction") or "KEEP",
        exact_delta=float(payload.get("exact_delta") or 0.0),
        current_value=float(payload.get("current_value") or 0.0),
        proposed_value=float(payload.get("proposed_value") or 0.0),
        confidence=float(payload.get("confidence") or 0.0),
        evidence_summary=str(payload.get("evidence_summary") or "Loaded from Phase 54 proposal pack."),
        supporting_evidence_ids=_tuple_text(payload.get("supporting_evidence_ids")),
        limitations=_tuple_text(payload.get("limitations")),
        risk_notes=_tuple_text(payload.get("risk_notes")),
        rollback_note=str(payload.get("rollback_note") or "No runtime rollback required; no settings were changed."),
        human_review_required=bool(payload.get("human_review_required", True)),
        auto_apply_allowed=bool(payload.get("auto_apply_allowed", False)),
        live_execution_allowed=bool(payload.get("live_execution_allowed", False)),
        status=payload.get("status") or "PROPOSED_FOR_HUMAN_REVIEW",
    )


def _blocked(payload: Mapping[str, Any]) -> BlockedCalibrationProposal:
    return BlockedCalibrationProposal(
        recommendation_id=str(payload.get("recommendation_id") or ""),
        reason=str(payload.get("reason") or "Blocked in Phase 54 proposal pack."),
        missing_evidence=_tuple_text(payload.get("missing_evidence")),
        limitations=_tuple_text(payload.get("limitations")),
        required_next_evidence=_tuple_text(payload.get("required_next_evidence")),
    )


def _checklist(payload: Mapping[str, Any]) -> ReviewChecklistItem:
    return ReviewChecklistItem(
        item_id=str(payload.get("item_id") or ""),
        question=str(payload.get("question") or "Review proposal evidence."),
        required=bool(payload.get("required", True)),
        status=str(payload.get("status") or "PENDING_HUMAN_REVIEW"),
        evidence_reference=str(payload.get("evidence_reference") or ""),
    )


def _risk_summary(payload: Mapping[str, Any]) -> ProposalRiskSummary:
    return ProposalRiskSummary(
        risk_level=str(payload.get("risk_level") or "UNKNOWN"),
        reasons=_tuple_text(payload.get("reasons")),
        evidence_quality=str(payload.get("evidence_quality") or "UNKNOWN"),
        synthetic_ratio=float(payload.get("synthetic_ratio") or 0.0),
        missing_observation_count=int(payload.get("missing_observation_count") or 0),
        invalid_observation_count=int(payload.get("invalid_observation_count") or 0),
        sparse_class_warnings=_tuple_text(payload.get("sparse_class_warnings")),
    )


def _load_existing_proposal_pack(payload: Mapping[str, Any]) -> CalibrationProposalPack:
    return CalibrationProposalPack(
        pack_id=str(payload.get("pack_id") or ""),
        created_at=str(payload.get("created_at") or payload.get("generated_at") or DETERMINISTIC_CREATED_AT),
        phase=str(payload.get("phase") or "54"),
        input_summary=dict(_mapping(payload.get("input_summary"))),
        proposals=tuple(_proposal(_mapping(item)) for item in payload.get("proposals", ())),
        blocked_recommendations=tuple(
            _blocked(_mapping(item)) for item in payload.get("blocked_recommendations", ())
        ),
        review_checklist=tuple(_checklist(_mapping(item)) for item in payload.get("review_checklist", ())),
        approval_requirements=_tuple_text(payload.get("approval_requirements")),
        safety_statement=str(payload.get("safety_statement") or SAFETY_SUMMARY),
        limitations=_tuple_text(payload.get("limitations")),
        risk_summary=_risk_summary(_mapping(payload.get("risk_summary"))),
        paper_only=bool(payload.get("paper_only", True)),
        auto_apply_allowed=bool(payload.get("auto_apply_allowed", False)),
        live_execution_allowed=bool(payload.get("live_execution_allowed", False)),
    )


def _load_or_build_proposal_pack(proposal_fixture: str | Path) -> CalibrationProposalPack:
    path = Path(proposal_fixture)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping) and isinstance(payload.get("proposals"), list):
        return _load_existing_proposal_pack(payload)
    return build_calibration_proposal_pack(path)


def build_approval_ledger(proposal_fixture: str | Path, review_fixture: str | Path) -> ApprovalLedger:
    pack = _load_or_build_proposal_pack(proposal_fixture)
    review_payload = load_review_payload(review_fixture)
    reviewer = reviewer_from_payload(review_payload, str(review_fixture))
    records = []
    change_request_items = []
    for item in review_items(review_payload):
        record, change_request = evaluate_review(pack, reviewer, item)
        records.append(record)
        if change_request is not None:
            change_request_items.append(change_request)
    decision_counts = dict(sorted(Counter(record.decision for record in records).items()))
    request_counts = dict(sorted(Counter(item.status for item in change_request_items).items()))
    limitation_summary = tuple(dict.fromkeys(
        limitation
        for record in records
        for limitation in record.limitation_summary
    ))
    ledger_id = stable_id(
        "cal",
        pack.pack_id,
        tuple(record.approval_record_id for record in records),
        tuple(item.change_request_id for item in change_request_items),
        reviewer.reviewer_id,
        reviewer.reviewed_at,
    )
    return ApprovalLedger(
        ledger_id=ledger_id,
        records=tuple(records),
        change_requests=tuple(change_request_items),
        counts_by_decision=decision_counts,
        counts_by_change_request_status=request_counts,
        blocked_count=decision_counts.get("BLOCKED", 0),
        approved_count=decision_counts.get("APPROVED_FOR_CHANGE_REQUEST", 0),
        invalid_count=decision_counts.get("INVALID_REVIEW", 0),
        generated_at=DETERMINISTIC_CREATED_AT,
        safety_summary=SAFETY_SUMMARY,
        limitation_summary=limitation_summary,
    )
