from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from sonic_xrpl.calibration_proposal.errors import CalibrationProposalError
from sonic_xrpl.calibration_proposal.models import (
    DETERMINISTIC_CREATED_AT,
    PHASE,
    BlockedCalibrationProposal,
    CalibrationParameterRef,
    CalibrationProposal,
    CalibrationProposalPack,
    ProposalRiskSummary,
    ReviewChecklistItem,
)
from sonic_xrpl.calibration_proposal.risk import summarize_proposal_risk
from sonic_xrpl.signals.evidence import stable_id


SAFETY_STATEMENT = (
    "Phase 54 calibration proposal packs are offline, paper-only, human-review-only artifacts. "
    "No settings were changed. Live execution remains blocked."
)

APPROVAL_REQUIREMENTS = (
    "A human reviewer must inspect every proposal, blocker, limitation, and evidence reference.",
    "Proposal pack generation does not change runtime settings.",
    "Future changes require a separate reviewed implementation phase.",
)

PARAMETERS: dict[str, dict[str, Any]] = {
    "signal_score_threshold": {
        "description": "Paper signal score boundary for BUY_CANDIDATE classification review.",
        "current_value": 0.70,
        "allowed_range": (0.0, 1.0),
    },
    "risk_score_threshold": {
        "description": "Paper risk score boundary for stricter candidate review.",
        "current_value": 0.30,
        "allowed_range": (0.0, 1.0),
    },
    "watch_threshold": {
        "description": "Paper watch boundary used by review workflows.",
        "current_value": 0.50,
        "allowed_range": (0.0, 1.0),
    },
    "avoid_threshold": {
        "description": "Paper avoid boundary used by review workflows.",
        "current_value": 0.80,
        "allowed_range": (0.0, 1.0),
    },
    "evidence_quality_threshold": {
        "description": "Minimum evidence quality threshold for future calibration review.",
        "current_value": 0.75,
        "allowed_range": (0.0, 1.0),
    },
    "unknown_penalty": {
        "description": "Penalty for unknown or missing paper evidence fields.",
        "current_value": 0.10,
        "allowed_range": (0.0, 1.0),
    },
    "synthetic_penalty": {
        "description": "Penalty for synthetic fixture evidence in calibration review.",
        "current_value": 1.00,
        "allowed_range": (0.0, 1.0),
    },
}


def load_recommendation_payload(path: str | Path) -> Mapping[str, Any]:
    fixture_path = Path(path)
    if not fixture_path.is_file():
        raise CalibrationProposalError(f"Calibration proposal fixture not found: {fixture_path}")
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CalibrationProposalError(f"Calibration proposal fixture is not valid JSON: {fixture_path}") from exc
    if isinstance(payload, list):
        recommendation_count = len([item for item in payload if isinstance(item, Mapping)])
        return {
            "paper_only": True,
            "live_execution_allowed": False,
            "readiness_result": {
                "readiness_id": stable_id("cr_missing", fixture_path, recommendation_count),
                "status": "NOT_READY",
                "confidence": 0.0,
                "blockers": (
                    "Phase 53 readiness snapshot is missing; pass calibration_readiness.json for exact proposals.",
                ),
                "warnings": (),
                "paper_only": True,
                "live_execution_allowed": False,
                "evidence_snapshot": {
                    "snapshot_id": stable_id("crs_missing", fixture_path, recommendation_count),
                    "corpus_case_count": 0,
                    "source_backed_case_count": 0,
                    "synthetic_case_count": 0,
                    "missing_observation_count": 0,
                    "invalid_observation_count": 0,
                    "quality_summary": {"quality_grade": "INSUFFICIENT"},
                },
            },
            "recommendations": payload,
            "limitations": ("readiness_snapshot_missing_for_recommendation_list",),
        }
    if not isinstance(payload, Mapping):
        raise CalibrationProposalError("Calibration proposal fixture must be a JSON object or recommendation array")
    return payload


def _recommendations(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    recommendations = payload.get("recommendations", [])
    if not isinstance(recommendations, list):
        raise CalibrationProposalError("recommendations must be an array")
    return tuple(item for item in recommendations if isinstance(item, Mapping))


def _readiness(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    result = payload.get("readiness_result", {})
    if not isinstance(result, Mapping):
        raise CalibrationProposalError("readiness_result must be an object")
    return result


def _snapshot(readiness_result: Mapping[str, Any]) -> Mapping[str, Any]:
    snapshot = readiness_result.get("evidence_snapshot", {})
    return snapshot if isinstance(snapshot, Mapping) else {}


def _status_supports_exact_proposals(readiness_result: Mapping[str, Any]) -> bool:
    return str(readiness_result.get("status")) in {"READY_FOR_HUMAN_REVIEW", "REVIEW_WITH_CAUTION"}


def _has_sparse_classes(readiness_result: Mapping[str, Any]) -> bool:
    return any("Sparse signal classes" in str(item) for item in readiness_result.get("warnings", []))


def _blocking_reason(readiness_result: Mapping[str, Any], risk: ProposalRiskSummary, recommendation: Mapping[str, Any]) -> str | None:
    direction = str(recommendation.get("direction") or "")
    if bool(recommendation.get("non_mutating", True)) is False:
        return "Source recommendation is not marked non-mutating."
    if direction in {"KEEP", "INSUFFICIENT_EVIDENCE"}:
        return "Recommendation does not request an exact threshold movement."
    if not _status_supports_exact_proposals(readiness_result):
        return "Readiness status does not support exact proposals."
    if readiness_result.get("blockers"):
        return "Readiness blockers are still present."
    if risk.synthetic_ratio > 0:
        return "Synthetic evidence cannot support exact proposals."
    if risk.invalid_observation_count > 0:
        return "Invalid numeric observations block exact proposals."
    if _has_sparse_classes(readiness_result):
        return "Sparse signal classes need more evidence."
    if not bool(recommendation.get("requires_human_review", True)):
        return "Source recommendation lacks required human-review flag."
    if bool(recommendation.get("live_execution_allowed", False)):
        return "Source recommendation violates live-execution safety state."
    return None


def _blocked(
    recommendation: Mapping[str, Any],
    reason: str,
    readiness_result: Mapping[str, Any],
) -> BlockedCalibrationProposal:
    recommendation_id = str(recommendation.get("recommendation_id") or stable_id("tr_missing", recommendation))
    blockers = tuple(str(item) for item in readiness_result.get("blockers", []))
    warnings = tuple(str(item) for item in readiness_result.get("warnings", []))
    return BlockedCalibrationProposal(
        recommendation_id=recommendation_id,
        reason=reason,
        missing_evidence=blockers or warnings or ("human-reviewed source-backed evidence",),
        limitations=tuple(str(item) for item in recommendation.get("limitations", [])) or warnings,
        required_next_evidence=(
            "additional source-backed paper outcomes",
            "complete provenance references",
            "human reviewer acceptance in a later phase",
        ),
    )


def _bounded(value: float, allowed_range: tuple[float, float]) -> float:
    lower, upper = allowed_range
    return round(max(lower, min(upper, value)), 2)


def _delta(direction: str) -> float:
    if direction == "REVIEW_INCREASE":
        return 0.02
    if direction == "REVIEW_DECREASE":
        return -0.02
    return 0.0


def _proposal(
    readiness_result: Mapping[str, Any],
    recommendation: Mapping[str, Any],
    source_path: str,
) -> CalibrationProposal:
    target = str(recommendation.get("target"))
    if target not in PARAMETERS:
        raise CalibrationProposalError(f"Unsupported calibration target: {target}")
    spec = PARAMETERS[target]
    current = float(spec["current_value"])
    allowed_range = tuple(float(item) for item in spec["allowed_range"])
    direction = str(recommendation.get("direction"))
    exact_delta = _delta(direction)
    proposed = _bounded(current + exact_delta, allowed_range)  # type: ignore[arg-type]
    recommendation_id = str(recommendation.get("recommendation_id"))
    readiness_id = str(readiness_result.get("readiness_id"))
    evidence_refs = tuple(str(item) for item in recommendation.get("evidence_refs", []))
    parameter_ref = CalibrationParameterRef(
        namespace="paper_calibration",
        name=target,  # type: ignore[arg-type]
        description=str(spec["description"]),
        current_value=current,
        proposed_value=proposed,
        value_type="ratio",
        allowed_range=allowed_range,  # type: ignore[arg-type]
        unit="ratio",
        source=source_path,
    )
    proposal_id = stable_id(
        "cp",
        readiness_id,
        recommendation_id,
        target,
        direction,
        current,
        proposed,
        evidence_refs,
    )
    return CalibrationProposal(
        proposal_id=proposal_id,
        created_at=DETERMINISTIC_CREATED_AT,
        phase=PHASE,
        source_readiness_id=readiness_id,
        source_recommendation_id=recommendation_id,
        parameter_ref=parameter_ref,
        direction=direction,  # type: ignore[arg-type]
        exact_delta=round(proposed - current, 2),
        current_value=current,
        proposed_value=proposed,
        confidence=round(float(recommendation.get("confidence") or 0.0), 2),
        evidence_summary=str(recommendation.get("rationale") or "No rationale provided."),
        supporting_evidence_ids=evidence_refs,
        limitations=tuple(str(item) for item in recommendation.get("limitations", [])),
        risk_notes=("Small deterministic review delta only.", "No settings were changed."),
        rollback_note="No runtime rollback is required unless a later phase changes settings; revert this proposal pack if needed.",
        human_review_required=True,
        auto_apply_allowed=False,
        live_execution_allowed=False,
    )


def _checklist(readiness_id: str, proposal_ids: tuple[str, ...]) -> tuple[ReviewChecklistItem, ...]:
    items = (
        ("evidence_review", "Verify source-backed paper evidence and provenance.", readiness_id),
        ("safety_review", "Verify no runtime setting change is included in this pack.", readiness_id),
        ("proposal_review", "Review each before and after value.", ",".join(proposal_ids) or "no exact proposals"),
        ("rollback_review", "Confirm rollback is a normal revert of Phase 54.", readiness_id),
    )
    return tuple(
        ReviewChecklistItem(
            item_id=stable_id("pci", key, reference),
            question=question,
            required=True,
            status="PENDING_HUMAN_REVIEW",
            evidence_reference=reference,
        )
        for key, question, reference in items
    )


def build_calibration_proposal_pack(path: str | Path) -> CalibrationProposalPack:
    payload = load_recommendation_payload(path)
    source_path = str(path)
    readiness_result = _readiness(payload)
    recommendations = _recommendations(payload)
    risk = summarize_proposal_risk(readiness_result)
    snapshot = _snapshot(readiness_result)
    proposals: list[CalibrationProposal] = []
    blocked: list[BlockedCalibrationProposal] = []

    for recommendation in recommendations:
        reason = _blocking_reason(readiness_result, risk, recommendation)
        if reason:
            blocked.append(_blocked(recommendation, reason, readiness_result))
            continue
        proposals.append(_proposal(readiness_result, recommendation, source_path))

    limitations = tuple(dict.fromkeys((
        *(str(item) for item in payload.get("limitations", [])),
        *(str(item) for item in readiness_result.get("warnings", [])),
        *(str(item) for item in readiness_result.get("blockers", [])),
    )))
    input_summary = {
        "source_file": source_path,
        "readiness_id": str(readiness_result.get("readiness_id") or ""),
        "readiness_status": str(readiness_result.get("status") or ""),
        "recommendation_count": len(recommendations),
        "proposal_count": len(proposals),
        "blocked_count": len(blocked),
        "corpus_case_count": int(snapshot.get("corpus_case_count") or 0),
        "source_backed_case_count": int(snapshot.get("source_backed_case_count") or 0),
        "synthetic_case_count": int(snapshot.get("synthetic_case_count") or 0),
    }
    proposal_ids = tuple(item.proposal_id for item in proposals)
    blocked_ids = tuple(item.recommendation_id for item in blocked)
    pack_id = stable_id(
        "cpp",
        input_summary,
        proposal_ids,
        blocked_ids,
        risk.risk_level,
        SAFETY_STATEMENT,
    )
    return CalibrationProposalPack(
        pack_id=pack_id,
        created_at=DETERMINISTIC_CREATED_AT,
        phase=PHASE,
        input_summary=input_summary,
        proposals=tuple(proposals),
        blocked_recommendations=tuple(blocked),
        review_checklist=_checklist(str(readiness_result.get("readiness_id") or ""), proposal_ids),
        approval_requirements=APPROVAL_REQUIREMENTS,
        safety_statement=SAFETY_STATEMENT,
        limitations=limitations,
        risk_summary=risk,
        paper_only=True,
        auto_apply_allowed=False,
        live_execution_allowed=False,
    )
