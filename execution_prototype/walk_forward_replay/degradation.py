"""Phase 44: Strategy Degradation Warning Generator.

Detects patterns that indicate degradation, instability, or data quality issues.
All warnings include evidence, recommended_human_action, prohibited_auto_action.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .models import StrategyDegradationWarning, StrategyStabilityProfile, WalkForwardEvaluation, _stable_id

PROHIBITED_AUTO = "Automated live trading, parameter mutation, model self-modification"


def _safe_dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _warning_id(evidence: List[str]) -> str:
    combined = "|".join(sorted(evidence))
    return _stable_id({"evidence": combined})


def _make_warning(
    dataset_id: str,
    strategy_id: str,
    warning_type: str,
    severity: str,
    evidence: List[str],
    recommended_human_action: str,
) -> StrategyDegradationWarning:
    wid = _warning_id([strategy_id, dataset_id, warning_type] + evidence[:3])
    return StrategyDegradationWarning(
        warning_id=wid,
        dataset_id=dataset_id,
        strategy_id=strategy_id,
        warning_type=warning_type,
        severity=severity,
        evidence=evidence,
        recommended_human_action=recommended_human_action,
        prohibited_auto_action=PROHIBITED_AUTO,
    )


def generate_degradation_warnings(
    evaluations: List[WalkForwardEvaluation],
    profiles: List[StrategyStabilityProfile],
    dataset: Dict[str, Any],
    tournament: Optional[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[StrategyDegradationWarning]:
    """Generate all degradation warnings for all strategies."""
    warnings: List[StrategyDegradationWarning] = []

    dataset_id = dataset.get("manifest", {}).get("dataset_id", "unknown_dataset")
    dataset_quality = dataset.get("quality_report", {}).get("quality_score", 50)
    warning_threshold = config.get("max_score_drop_warning", -15)
    critical_threshold = config.get("max_score_drop_critical", -30)

    profile_by_strategy: Dict[str, StrategyStabilityProfile] = {
        p.strategy_id: p for p in profiles
    }

    by_strategy: Dict[str, List[WalkForwardEvaluation]] = {}
    for ev in evaluations:
        by_strategy.setdefault(ev.strategy_id, []).append(ev)

    quality_report = dataset.get("quality_report", {})
    future_leakage = quality_report.get("future_leakage_count", 0) > 0
    if not future_leakage:
        for wtype_records in dataset.get("records_by_window", {}).values():
            if any(r.get("future_leakage") for r in wtype_records):
                future_leakage = True
                break

    unsupported_batch = False
    xahau_hook = False
    for wtype_records in dataset.get("records_by_window", {}).values():
        for r in wtype_records:
            if r.get("unsupported_batch_context"):
                unsupported_batch = True
            if r.get("xahau_hook_context"):
                xahau_hook = True

    for strategy_id, strat_evals in by_strategy.items():
        sorted_evals = sorted(strat_evals, key=lambda e: e.chronological_order)
        profile = profile_by_strategy.get(strategy_id)

        scores = [e.evaluation_score for e in sorted_evals]
        deltas = [e.score_delta for e in sorted_evals]

        # 1. Rolling score decay.
        if len(scores) >= 3:
            first_half = scores[: len(scores) // 2]
            second_half = scores[len(scores) // 2 :]
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            if second_avg < first_avg - 10:
                severity = "critical" if second_avg < first_avg - 25 else "warning"
                warnings.append(_make_warning(
                    dataset_id, strategy_id, "rolling_score_decay", severity,
                    evidence=[
                        f"first_half_avg={first_avg:.1f}",
                        f"second_half_avg={second_avg:.1f}",
                        f"decay={first_avg - second_avg:.1f}",
                    ],
                    recommended_human_action=(
                        "Human should review strategy performance trend and consider"
                        " pausing or retiring from paper pool."
                    ),
                ))

        # 1b. Consistent score drop below warning threshold (but above critical).
        warning_drop_count = sum(
            1 for d in deltas if warning_threshold > d >= critical_threshold
        )
        if warning_drop_count >= max(1, len(deltas) // 2):
            warnings.append(_make_warning(
                dataset_id, strategy_id, "rolling_score_decay", "warning",
                evidence=[
                    f"windows_with_score_drop={warning_drop_count}",
                    f"warning_threshold={warning_threshold}",
                ],
                recommended_human_action=(
                    "Human should review consistent score drop pattern."
                    " Strategy may be losing effectiveness across windows."
                ),
            ))

        # 2. Evaluation collapse.
        collapse_count = sum(1 for d in deltas if d < critical_threshold)
        if collapse_count > 0:
            severity = "critical" if collapse_count >= 2 else "warning"
            warnings.append(_make_warning(
                dataset_id, strategy_id, "evaluation_collapse", severity,
                evidence=[
                    f"collapse_windows={collapse_count}",
                    f"critical_threshold={critical_threshold}",
                ],
                recommended_human_action=(
                    "Human should investigate root cause of evaluation score collapse"
                    " and pause paper testing pending review."
                ),
            ))

        # 3. Volatility spike.
        if profile and profile.score_volatility:
            try:
                vol = float(profile.score_volatility)
                if vol > 20:
                    severity = "critical" if vol > 35 else "warning"
                    warnings.append(_make_warning(
                        dataset_id, strategy_id, "volatility_spike", severity,
                        evidence=[f"score_volatility={vol:.2f}"],
                        recommended_human_action=(
                            "Human should review high score volatility."
                            " Strategy may be regime-sensitive."
                        ),
                    ))
            except (TypeError, ValueError):
                pass

        # 4. Metadata dependency.
        meta_low = [e for e in sorted_evals if _safe_dec(e.metadata_backed_rate) < Decimal("0.60")]
        if meta_low:
            warnings.append(_make_warning(
                dataset_id, strategy_id, "metadata_dependency", "caution",
                evidence=[
                    f"windows_with_low_metadata_rate={len(meta_low)}",
                    f"min_metadata_rate={min(_safe_dec(e.metadata_backed_rate) for e in meta_low)}",
                ],
                recommended_human_action=(
                    "Human should verify metadata quality before relying on paper signals."
                ),
            ))

        # 5. Liquidity dependency.
        liq_low = [e for e in sorted_evals if _safe_dec(e.liquidity_backed_rate) < Decimal("0.60")]
        if liq_low:
            warnings.append(_make_warning(
                dataset_id, strategy_id, "liquidity_dependency", "caution",
                evidence=[
                    f"windows_with_low_liquidity_rate={len(liq_low)}",
                ],
                recommended_human_action=(
                    "Human should verify liquidity conditions before extending paper testing."
                ),
            ))

        # 6. Unknown outcome dependency.
        unknown_high = [e for e in sorted_evals if _safe_dec(e.unknown_outcome_rate) > Decimal("0.30")]
        if unknown_high:
            severity = "warning" if len(unknown_high) > 1 else "caution"
            warnings.append(_make_warning(
                dataset_id, strategy_id, "unknown_outcome_dependency", severity,
                evidence=[
                    f"windows_with_high_unknown_rate={len(unknown_high)}",
                    f"max_unknown_rate={max(_safe_dec(e.unknown_outcome_rate) for e in unknown_high)}",
                ],
                recommended_human_action=(
                    "Human should investigate high unknown outcome rate."
                    " Results may not reflect real strategy performance."
                ),
            ))

        # 7. Sample size fragility.
        small_sample = [e for e in sorted_evals if e.sample_size < config.get("min_sample_size", 5)]
        if small_sample:
            warnings.append(_make_warning(
                dataset_id, strategy_id, "sample_size_fragility", "caution",
                evidence=[
                    f"windows_with_small_sample={len(small_sample)}",
                    f"min_sample_size={min(e.sample_size for e in small_sample)}",
                ],
                recommended_human_action=(
                    "Human should collect more data before drawing conclusions from this strategy."
                ),
            ))

        # 8. Dataset quality dependency.
        if dataset_quality < 50:
            warnings.append(_make_warning(
                dataset_id, strategy_id, "dataset_quality_dependency", "warning",
                evidence=[f"dataset_quality_score={dataset_quality}"],
                recommended_human_action=(
                    "Human should improve dataset quality to >= 60 before"
                    " trusting paper evaluation results."
                ),
            ))

        # 9. Regime shift sensitive.
        if len(scores) >= 4:
            mid = len(scores) // 2
            first_best = max(scores[:mid])
            second_worst = min(scores[mid:])
            if first_best - second_worst > 30:
                warnings.append(_make_warning(
                    dataset_id, strategy_id, "regime_shift_sensitive", "warning",
                    evidence=[
                        f"first_half_peak={first_best}",
                        f"second_half_trough={second_worst}",
                        f"range={first_best - second_worst}",
                    ],
                    recommended_human_action=(
                        "Human should assess whether strategy is sensitive to market regime changes."
                    ),
                ))

        # 10. Phase43 overfit dependency.
        if tournament:
            for result in tournament.get("tournament_results", []):
                if result.get("strategy_id") == strategy_id:
                    overfit_score = result.get("overfitting_score", 0)
                    if overfit_score > 60:
                        warnings.append(_make_warning(
                            dataset_id, strategy_id, "phase43_overfit_dependency", "warning",
                            evidence=[f"phase43_overfitting_score={overfit_score}"],
                            recommended_human_action=(
                                "Human should review Phase 43 overfitting score before"
                                " extending paper tests."
                            ),
                        ))
                    break

        # 11. Future leakage dependency.
        if future_leakage:
            warnings.append(_make_warning(
                dataset_id, strategy_id, "future_leakage_dependency", "critical",
                evidence=["future_leakage_detected_in_dataset"],
                recommended_human_action=(
                    "Human must rebuild dataset without future leakage before"
                    " trusting any paper evaluation scores."
                ),
            ))

        # 12. Unsupported protocol context.
        if unsupported_batch:
            warnings.append(_make_warning(
                dataset_id, strategy_id, "unsupported_protocol_context", "critical",
                evidence=["unsupported_batch_context_detected"],
                recommended_human_action=(
                    "Human should verify XRPL Batch transaction context is not present."
                    " Unsupported protocol context invalidates evaluation scores."
                ),
            ))
        elif xahau_hook:
            warnings.append(_make_warning(
                dataset_id, strategy_id, "unsupported_protocol_context", "warning",
                evidence=["xahau_hook_context_detected"],
                recommended_human_action=(
                    "Human should verify Xahau/Hook context is not affecting XRPL paper results."
                ),
            ))

    return warnings
