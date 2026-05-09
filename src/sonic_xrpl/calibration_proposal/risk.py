from __future__ import annotations

from typing import Any, Mapping

from sonic_xrpl.calibration_proposal.models import ProposalRiskSummary


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def summarize_proposal_risk(readiness_result: Mapping[str, Any]) -> ProposalRiskSummary:
    snapshot = readiness_result.get("evidence_snapshot", {})
    if not isinstance(snapshot, Mapping):
        snapshot = {}
    total_cases = int(snapshot.get("corpus_case_count") or 0)
    synthetic_cases = int(snapshot.get("synthetic_case_count") or 0)
    missing_count = int(snapshot.get("missing_observation_count") or 0)
    invalid_count = int(snapshot.get("invalid_observation_count") or 0)
    synthetic_ratio = _ratio(synthetic_cases, total_cases)
    warnings = tuple(str(item) for item in readiness_result.get("warnings", []) if "Sparse signal classes" in str(item))
    quality = snapshot.get("quality_summary", {})
    quality_grade = str(quality.get("quality_grade") if isinstance(quality, Mapping) else "unknown")

    reasons: list[str] = []
    if synthetic_ratio > 0:
        reasons.append("Synthetic evidence is present and cannot support exact proposals.")
    if missing_count:
        reasons.append("Missing observations remain explicit in the evidence set.")
    if invalid_count:
        reasons.append("Invalid numeric observations block exact proposals.")
    if warnings:
        reasons.append("Sparse signal classes limit confidence.")
    if not reasons:
        reasons.append("Source-backed paper evidence is sufficient for a human review packet.")

    if invalid_count or synthetic_ratio > 0:
        risk_level = "HIGH"
    elif missing_count or warnings:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return ProposalRiskSummary(
        risk_level=risk_level,
        reasons=tuple(reasons),
        evidence_quality=quality_grade,
        synthetic_ratio=synthetic_ratio,
        missing_observation_count=missing_count,
        invalid_observation_count=invalid_count,
        sparse_class_warnings=warnings,
    )
