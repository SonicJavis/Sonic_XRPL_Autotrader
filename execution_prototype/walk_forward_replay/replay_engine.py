"""Phase 44: Walk-Forward Replay Engine.

For each walk-forward window × strategy, compute training/evaluation scores
and quality metrics. No network calls. No wallet. No signing.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from .models import WalkForwardEvaluation, WalkForwardWindow, _stable_id

PROHIBITED_LIVE = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."

# Fallback rates when Phase 42/43 data is unavailable (conservative defaults).
_DEFAULT_UNKNOWN_RATE = "0.50"
_DEFAULT_METADATA_RATE = "0.50"
_DEFAULT_LIQUIDITY_RATE = "0.50"

_MIN_SAMPLE_SIZE_DEFAULT = 5


def _safe_dec(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _mean_score(scores: List[int]) -> int:
    if not scores:
        return 0
    return int(sum(scores) / len(scores))


def _extract_strategy_ids(tournament: Optional[Dict[str, Any]]) -> List[str]:
    if not tournament:
        return []
    ids: List[str] = []
    for r in tournament.get("tournament_results", []):
        sid = r.get("strategy_id")
        if sid and sid not in ids:
            ids.append(sid)
    return ids


def _tournament_score_for_window(
    tournament: Optional[Dict[str, Any]],
    strategy_id: str,
    window_id: str,
) -> Optional[int]:
    """Look up Phase 43 quality_weighted_score for a strategy/window combination."""
    if not tournament:
        return None
    for ev in tournament.get("strategy_window_evaluations", []):
        if ev.get("strategy_id") == strategy_id and ev.get("window_id") == window_id:
            score = ev.get("quality_weighted_score")
            if score is not None:
                try:
                    return int(score)
                except (TypeError, ValueError):
                    pass
    return None


def _tournament_rates_for_window(
    tournament: Optional[Dict[str, Any]],
    strategy_id: str,
    window_id: str,
) -> Dict[str, str]:
    """Extract rate strings from Phase 43 evaluation for a strategy/window."""
    defaults = {
        "unknown_outcome_rate": _DEFAULT_UNKNOWN_RATE,
        "metadata_backed_rate": _DEFAULT_METADATA_RATE,
        "liquidity_backed_rate": _DEFAULT_LIQUIDITY_RATE,
        "records_evaluated": 0,
    }
    if not tournament:
        return defaults
    for ev in tournament.get("strategy_window_evaluations", []):
        if ev.get("strategy_id") == strategy_id and ev.get("window_id") == window_id:
            return {
                "unknown_outcome_rate": str(ev.get("unknown_outcome_rate", _DEFAULT_UNKNOWN_RATE)),
                "metadata_backed_rate": str(ev.get("metadata_backed_rate", _DEFAULT_METADATA_RATE)),
                "liquidity_backed_rate": str(ev.get("liquidity_backed_rate", _DEFAULT_LIQUIDITY_RATE)),
                "records_evaluated": ev.get("records_evaluated", 0),
            }
    return defaults


def _compute_confidence_band(
    sample_size: int,
    windows_in_training: int,
    limitations: List[str],
) -> str:
    if sample_size < 5 or windows_in_training < 1:
        return "low"
    if any(
        lim in limitations
        for lim in (
            "unknown_outcome_rate_high",
            "metadata_backed_rate_low",
            "liquidity_backed_rate_low",
            "future_leakage_detected",
            "dataset_quality_low",
        )
    ):
        return "low"
    if sample_size >= 20 and windows_in_training >= 3:
        return "high"
    return "medium"


def _build_evaluation_limitations(
    unknown_rate: Decimal,
    metadata_rate: Decimal,
    liquidity_rate: Decimal,
    sample_size: int,
    dataset_quality: int,
    dataset: Dict[str, Any],
) -> List[str]:
    lims: List[str] = []
    if unknown_rate > Decimal("0.30"):
        lims.append("unknown_outcome_rate_high")
    if metadata_rate < Decimal("0.60"):
        lims.append("metadata_backed_rate_low")
    if liquidity_rate < Decimal("0.60"):
        lims.append("liquidity_backed_rate_low")
    if sample_size < 5:
        lims.append("sample_size_below_minimum")
    if dataset_quality < 50:
        lims.append("dataset_quality_low")

    quality_report = dataset.get("quality_report", {})
    if quality_report.get("future_leakage_count", 0) > 0:
        lims.append("future_leakage_detected")

    records = []
    for wtype_records in dataset.get("records_by_window", {}).values():
        records.extend(wtype_records)
    if any(r.get("unsupported_batch_context") for r in records):
        lims.append("unsupported_batch_context")
    if any(r.get("xahau_hook_context") for r in records):
        lims.append("xahau_hook_context")

    return lims


def run_replay(
    dataset: Dict[str, Any],
    tournament: Optional[Dict[str, Any]],
    windows: List[WalkForwardWindow],
    config: Dict[str, Any],
) -> List[WalkForwardEvaluation]:
    """Run the walk-forward replay for all strategies across all windows."""
    if not windows:
        return []

    dataset_id = dataset.get("manifest", {}).get("dataset_id", "unknown_dataset")
    dataset_quality = dataset.get("quality_report", {}).get("quality_score", 50)

    strategy_ids = _extract_strategy_ids(tournament)
    if not strategy_ids:
        strategy_ids = ["baseline_strategy"]

    min_sample_size = config.get("min_sample_size", _MIN_SAMPLE_SIZE_DEFAULT)
    evaluations: List[WalkForwardEvaluation] = []

    # Accumulate per-strategy evaluation scores as we walk forward.
    strategy_prior_scores: Dict[str, List[int]] = {sid: [] for sid in strategy_ids}

    for wf_window in windows:
        eval_window_id = wf_window.evaluation_window_id

        for strategy_id in strategy_ids:
            eval_score = _tournament_score_for_window(tournament, strategy_id, eval_window_id)
            if eval_score is None:
                eval_score = dataset_quality

            rates = _tournament_rates_for_window(tournament, strategy_id, eval_window_id)
            unknown_rate = _safe_dec(rates["unknown_outcome_rate"], Decimal("0.50"))
            metadata_rate = _safe_dec(rates["metadata_backed_rate"], Decimal("0.50"))
            liquidity_rate = _safe_dec(rates["liquidity_backed_rate"], Decimal("0.50"))

            sample_size = int(rates.get("records_evaluated", 0))
            if sample_size < 1:
                sample_size = wf_window.evaluation_record_count

            prior_scores = strategy_prior_scores[strategy_id]
            training_score = _mean_score(prior_scores) if prior_scores else dataset_quality

            score_delta = eval_score - training_score

            limitations = _build_evaluation_limitations(
                unknown_rate, metadata_rate, liquidity_rate,
                sample_size, dataset_quality, dataset,
            )

            confidence_band = _compute_confidence_band(
                sample_size,
                len(wf_window.training_window_ids),
                limitations,
            )

            eval_id = _stable_id({
                "walk_window_id": wf_window.walk_window_id,
                "strategy_id": strategy_id,
                "dataset_id": dataset_id,
                "chronological_order": wf_window.chronological_order,
            })

            evaluation = WalkForwardEvaluation(
                evaluation_id=eval_id,
                walk_window_id=wf_window.walk_window_id,
                dataset_id=dataset_id,
                strategy_id=strategy_id,
                chronological_order=wf_window.chronological_order,
                training_score=training_score,
                evaluation_score=eval_score,
                score_delta=score_delta,
                unknown_outcome_rate=str(unknown_rate),
                metadata_backed_rate=str(metadata_rate),
                liquidity_backed_rate=str(liquidity_rate),
                sample_size=sample_size,
                confidence_band=confidence_band,
                limitations=limitations,
            )
            evaluations.append(evaluation)

            # Accumulate this evaluation score for subsequent training score calculations.
            strategy_prior_scores[strategy_id].append(eval_score)

    return evaluations
