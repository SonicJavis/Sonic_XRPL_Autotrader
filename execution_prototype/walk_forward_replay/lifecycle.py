"""Phase 44: Paper Strategy Lifecycle Recommendations.

Maps stability profiles + warnings to paper-only lifecycle statuses.
NEVER produces live trading authorization.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import (
    PaperStrategyLifecycleRecommendation,
    StrategyDegradationWarning,
    StrategyStabilityProfile,
    _stable_id,
)

PROHIBITED_LIVE = (
    "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION. LIVE TRADING FORBIDDEN."
)

# Lifecycle statuses.
STATUS_CONTINUE = "continue_paper_testing"
STATUS_SCRUTINY = "increase_paper_scrutiny"
STATUS_PAUSE = "pause_paper_testing"
STATUS_RETIRE = "retire_from_current_paper_pool"
STATUS_INSUFFICIENT = "insufficient_data"


def _recommendation_id(dataset_id: str, strategy_id: str, lifecycle_status: str) -> str:
    return _stable_id({
        "dataset_id": dataset_id,
        "strategy_id": strategy_id,
        "lifecycle_status": lifecycle_status,
        "type": "lifecycle_recommendation",
    })


def generate_lifecycle_recommendations(
    profiles: List[StrategyStabilityProfile],
    warnings: List[StrategyDegradationWarning],
    dataset: Dict[str, Any],
    config: Dict[str, Any],
) -> List[PaperStrategyLifecycleRecommendation]:
    """Generate lifecycle recommendations for each strategy. Paper-only."""
    recommendations: List[PaperStrategyLifecycleRecommendation] = []

    dataset_id = dataset.get("manifest", {}).get("dataset_id", "unknown_dataset")

    warnings_by_strategy: Dict[str, List[StrategyDegradationWarning]] = {}
    for w in warnings:
        warnings_by_strategy.setdefault(w.strategy_id, []).append(w)

    for profile in profiles:
        strategy_id = profile.strategy_id
        strat_warnings = warnings_by_strategy.get(strategy_id, [])

        critical_warnings = [w for w in strat_warnings if w.severity == "critical"]
        warning_level = [w for w in strat_warnings if w.severity == "warning"]

        unsupported_batch = any(
            w.warning_type == "unsupported_protocol_context"
            and "unsupported_batch_context" in " ".join(w.evidence)
            for w in strat_warnings
        )
        future_leakage = any(
            w.warning_type == "future_leakage_dependency"
            for w in strat_warnings
        )
        collapse = any(
            w.warning_type == "evaluation_collapse"
            for w in strat_warnings
        )
        rolling_decay = any(
            w.warning_type == "rolling_score_decay"
            for w in strat_warnings
        )

        # Determine lifecycle status.
        if profile.stability_band == "insufficient_data":
            lifecycle_status = STATUS_INSUFFICIENT
            reason = (
                f"Insufficient walk-forward windows ({profile.windows_evaluated}) to"
                " assess stability. Collect more data."
            )
            required_human_action = (
                "Human should collect more historical data and re-run walk-forward replay."
            )

        elif future_leakage or unsupported_batch:
            lifecycle_status = STATUS_RETIRE
            reason = (
                "Critical data integrity issues detected: "
                + ("future leakage" if future_leakage else "")
                + (" and " if future_leakage and unsupported_batch else "")
                + ("unsupported Batch context" if unsupported_batch else "")
                + ". Dataset must be rebuilt."
            )
            required_human_action = (
                "Human must rebuild dataset without future leakage or unsupported protocol"
                " context before re-evaluating this strategy."
            )

        elif profile.stability_band == "unstable" or collapse or len(critical_warnings) >= 2:
            lifecycle_status = STATUS_PAUSE
            reason = (
                f"Strategy is unstable (stability_score={profile.stability_score},"
                f" stability_band={profile.stability_band},"
                f" critical_warnings={len(critical_warnings)})."
            )
            required_human_action = (
                "Human should pause paper testing and investigate root causes of instability"
                " before continuing."
            )

        elif rolling_decay or len(critical_warnings) >= 1 or profile.stability_band == "watch":
            lifecycle_status = STATUS_SCRUTINY
            reason = (
                f"Strategy shows signs of degradation or instability"
                f" (stability_score={profile.stability_score},"
                f" degradation_count={profile.degradation_count})."
            )
            required_human_action = (
                "Human should increase monitoring frequency and review degradation warnings"
                " before next paper cycle."
            )

        elif profile.stability_band == "stable":
            lifecycle_status = STATUS_CONTINUE
            reason = (
                f"Strategy appears stable across walk-forward windows"
                f" (stability_score={profile.stability_score},"
                f" windows_evaluated={profile.windows_evaluated})."
            )
            required_human_action = (
                "Human should review stability profile and approve continuation of paper testing."
            )

        else:
            lifecycle_status = STATUS_SCRUTINY
            reason = "Mixed results; manual review recommended."
            required_human_action = (
                "Human should review all warnings and stability metrics before continuing."
            )

        recommendation_id = _recommendation_id(dataset_id, strategy_id, lifecycle_status)

        rec = PaperStrategyLifecycleRecommendation(
            recommendation_id=recommendation_id,
            dataset_id=dataset_id,
            strategy_id=strategy_id,
            lifecycle_status=lifecycle_status,
            reason=reason,
            required_human_action=required_human_action,
            prohibited_live_action=PROHIBITED_LIVE,
            limitations=list(profile.limitations),
        )
        recommendations.append(rec)

    return recommendations
