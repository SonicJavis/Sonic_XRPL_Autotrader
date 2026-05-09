from __future__ import annotations

from sonic_xrpl.calibration_review.models import CalibrationReadinessResult, ThresholdRecommendation
from sonic_xrpl.signals.evidence import stable_id


def _recommendation(target: str, direction: str, rationale: str, refs: tuple[str, ...], confidence: float) -> ThresholdRecommendation:
    return ThresholdRecommendation(
        recommendation_id=stable_id("tr", target, direction, rationale, refs, confidence),
        target=target,  # type: ignore[arg-type]
        direction=direction,  # type: ignore[arg-type]
        rationale=rationale,
        evidence_refs=refs,
        confidence=confidence,
        non_mutating=True,
        requires_human_review=True,
        live_execution_allowed=False,
    )


def build_threshold_recommendations(result: CalibrationReadinessResult) -> tuple[ThresholdRecommendation, ...]:
    snapshot = result.evidence_snapshot
    refs = snapshot.source_files
    recommendations: list[ThresholdRecommendation] = []
    if result.status in {"NOT_READY", "NEEDS_MORE_EVIDENCE"}:
        for target in (
            "signal_score_threshold",
            "risk_score_threshold",
            "watch_threshold",
            "avoid_threshold",
        ):
            recommendations.append(_recommendation(
                target,
                "INSUFFICIENT_EVIDENCE",
                "Evidence is not ready for calibration review; keep current settings unchanged.",
                refs,
                min(result.confidence, 0.4),
            ))
    else:
        has_sparse_classes = any("Sparse signal classes:" in warning for warning in result.warnings)
        watch_count = snapshot.signal_type_counts.get("WATCH", 0)
        watch_wins = snapshot.favorable_outcome_counts.get("WATCH", 0)
        buy_count = snapshot.signal_type_counts.get("BUY_CANDIDATE", 0)
        buy_wins = snapshot.favorable_outcome_counts.get("BUY_CANDIDATE", 0)
        if watch_count >= 2 and watch_wins / watch_count >= 0.5 and not has_sparse_classes:
            recommendations.append(_recommendation(
                "watch_threshold",
                "REVIEW_DECREASE",
                "WATCH paper outcomes look favorable enough to consider a human review of whether the watch boundary is too strict.",
                refs,
                min(result.confidence, 0.65),
            ))
        else:
            recommendations.append(_recommendation(
                "watch_threshold",
                "KEEP",
                "WATCH evidence is sparse or mixed; keep current setting unchanged.",
                refs,
                min(result.confidence, 0.6),
            ))
        if buy_count and buy_wins / buy_count < 0.5 and not has_sparse_classes:
            recommendations.append(_recommendation(
                "signal_score_threshold",
                "REVIEW_INCREASE",
                "BUY_CANDIDATE paper outcomes are weak enough to consider stricter human-reviewed evidence requirements.",
                refs,
                min(result.confidence, 0.65),
            ))
        else:
            recommendations.append(_recommendation(
                "signal_score_threshold",
                "KEEP",
                "Available source-backed paper outcomes do not justify a change without human review.",
                refs,
                min(result.confidence, 0.6),
            ))

    source_ratio = (
        snapshot.source_backed_case_count / snapshot.corpus_case_count
        if snapshot.corpus_case_count else 0.0
    )
    recommendations.append(_recommendation(
        "evidence_quality_threshold",
        "REVIEW_INCREASE" if source_ratio < 0.9 else "KEEP",
        "Recommendations are advisory only and do not mutate runtime configuration; source-backed evidence quality remains the gate for any future proposal.",
        refs,
        min(result.confidence, 0.7),
    ))
    recommendations.append(_recommendation(
        "unknown_penalty",
        "KEEP" if snapshot.missing_observation_count == 0 else "REVIEW_INCREASE",
        "Missing observations remain explicit and should continue to be penalized before any calibration proposal.",
        refs,
        min(result.confidence, 0.6),
    ))
    recommendations.append(_recommendation(
        "synthetic_penalty",
        "KEEP" if snapshot.synthetic_case_count == 0 else "INSUFFICIENT_EVIDENCE",
        "Synthetic cases can test code paths but cannot support calibration readiness.",
        refs,
        min(result.confidence, 0.6),
    ))
    return tuple(recommendations)
