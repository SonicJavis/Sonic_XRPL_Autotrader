"""Phase 44: Strategy Stability Profiles.

Groups evaluations by strategy and computes stability metrics with safety caps.
"""
from __future__ import annotations

import statistics
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .models import StrategyStabilityProfile, WalkForwardEvaluation, _stable_id


def _safe_dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _median_int(values: List[int]) -> int:
    if not values:
        return 0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) // 2
    return sorted_vals[mid]


def _has_future_leakage(dataset: Dict[str, Any]) -> bool:
    quality_report = dataset.get("quality_report", {})
    if quality_report.get("future_leakage_count", 0) > 0:
        return True
    for wtype_records in dataset.get("records_by_window", {}).values():
        if any(r.get("future_leakage") for r in wtype_records):
            return True
    return False


def _has_unsupported_batch_context(dataset: Dict[str, Any]) -> bool:
    for wtype_records in dataset.get("records_by_window", {}).values():
        if any(r.get("unsupported_batch_context") for r in wtype_records):
            return True
    return False


def _has_xahau_hook_context(dataset: Dict[str, Any]) -> bool:
    for wtype_records in dataset.get("records_by_window", {}).values():
        if any(r.get("xahau_hook_context") for r in wtype_records):
            return True
    return False


def compute_stability_profiles(
    evaluations: List[WalkForwardEvaluation],
    dataset_id: str,
    config: Dict[str, Any],
    dataset: Optional[Dict[str, Any]] = None,
) -> List[StrategyStabilityProfile]:
    """Compute StrategyStabilityProfile for each unique strategy in evaluations."""
    if not evaluations:
        return []

    if dataset is None:
        dataset = {}

    warning_threshold = config.get("max_score_drop_warning", -15)
    critical_threshold = config.get("max_score_drop_critical", -30)
    dataset_quality = dataset.get("quality_report", {}).get("quality_score", 50)

    future_leakage = _has_future_leakage(dataset)
    unsupported_batch = _has_unsupported_batch_context(dataset)
    xahau_hook = _has_xahau_hook_context(dataset)

    by_strategy: Dict[str, List[WalkForwardEvaluation]] = {}
    for ev in evaluations:
        by_strategy.setdefault(ev.strategy_id, []).append(ev)

    profiles: List[StrategyStabilityProfile] = []

    for strategy_id, strat_evals in by_strategy.items():
        # Sort chronologically.
        sorted_evals = sorted(strat_evals, key=lambda e: e.chronological_order)

        scores = [e.evaluation_score for e in sorted_evals]
        deltas = [e.score_delta for e in sorted_evals]
        n = len(scores)

        mean_score = int(sum(scores) / n) if n else 0
        median_score = _median_int(scores)
        worst_score = min(scores) if scores else 0
        best_score = max(scores) if scores else 0

        if n >= 2:
            try:
                volatility = statistics.stdev(scores)
            except statistics.StatisticsError:
                volatility = 0.0
        else:
            volatility = 0.0

        degradation_count = sum(1 for d in deltas if d < warning_threshold)
        critical_degradation_count = sum(1 for d in deltas if d < critical_threshold)

        # Stability score formula.
        volatility_penalty = config.get("volatility_penalty", 0.5)
        base_score = float(mean_score)
        score = base_score - (volatility_penalty * volatility)
        score -= degradation_count * 3
        score -= critical_degradation_count * 10

        # Apply caps.
        if future_leakage:
            score = min(score, 40.0)
        if dataset_quality < 50:
            score = min(score, 50.0)
        if unsupported_batch or xahau_hook:
            score = min(score, 60.0)

        stability_score = max(0, min(100, int(score)))

        # Stability band.
        if n < 2:
            stability_band = "insufficient_data"
        elif stability_score >= 75:
            stability_band = "stable"
        elif stability_score >= 50:
            stability_band = "watch"
        else:
            stability_band = "unstable"

        # Confidence band.
        if n < 3:
            confidence_band = "low"
        elif n <= 5:
            confidence_band = "medium"
        else:
            confidence_band = "high"

        # Cap confidence if there are many per-evaluation limitations.
        all_lims = [lim for ev in sorted_evals for lim in ev.limitations]
        high_impact_lims = {
            "future_leakage_detected",
            "unsupported_batch_context",
            "dataset_quality_low",
            "unknown_outcome_rate_high",
        }
        if any(lim in high_impact_lims for lim in all_lims):
            if confidence_band == "high":
                confidence_band = "medium"

        # Aggregate limitations.
        unique_lims: List[str] = []
        seen = set()
        for lim in all_lims:
            if lim not in seen:
                unique_lims.append(lim)
                seen.add(lim)
        if future_leakage and "future_leakage_detected" not in seen:
            unique_lims.append("future_leakage_detected")
        if unsupported_batch and "unsupported_batch_context" not in seen:
            unique_lims.append("unsupported_batch_context")
        if xahau_hook and "xahau_hook_context" not in seen:
            unique_lims.append("xahau_hook_context")

        stability_id = _stable_id({
            "dataset_id": dataset_id,
            "strategy_id": strategy_id,
            "windows_evaluated": n,
            "stability_band": stability_band,
        })

        profile = StrategyStabilityProfile(
            stability_id=stability_id,
            dataset_id=dataset_id,
            strategy_id=strategy_id,
            windows_evaluated=n,
            mean_evaluation_score=mean_score,
            median_evaluation_score=median_score,
            score_volatility=f"{volatility:.4f}",
            worst_evaluation_score=worst_score,
            best_evaluation_score=best_score,
            degradation_count=degradation_count,
            critical_degradation_count=critical_degradation_count,
            stability_score=stability_score,
            stability_band=stability_band,
            confidence_band=confidence_band,
            limitations=unique_lims,
        )
        profiles.append(profile)

    return profiles
