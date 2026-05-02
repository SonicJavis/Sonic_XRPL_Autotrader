from __future__ import annotations
import hashlib
import statistics
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from .models import DatasetStrategyDefinition, StrategyWindowEvaluation
from .strategy_registry import STRATEGY_EVALUATORS

OUTCOME_KEYS = frozenset({
    "outcome", "pnl_pct", "win", "loss",
    "paper_outcome", "paper_pnl_pct", "resolved_at", "outcome_source",
})


def _get_eval_id(strategy_id: str, dataset_id: str, window_id: str, window_type: str) -> str:
    raw = "|".join(sorted([strategy_id, dataset_id, window_id, window_type]))
    return hashlib.sha256(raw.encode()).hexdigest()


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


class WindowEvaluator:
    def evaluate(
        self,
        strategy_def: DatasetStrategyDefinition,
        records: List[Dict],
        window_id: str,
        window_type: str,
        dataset_id: str,
        dataset_quality_score: int,
    ) -> StrategyWindowEvaluation:
        evaluation_id = _get_eval_id(
            strategy_def.strategy_id, dataset_id, window_id, window_type
        )
        limitations: List[str] = []

        if not records:
            return StrategyWindowEvaluation(
                evaluation_id=evaluation_id,
                dataset_id=dataset_id,
                window_id=window_id,
                window_type=window_type,
                strategy_id=strategy_def.strategy_id,
                records_evaluated=0,
                signals_generated=0,
                accepted_signals=0,
                rejected_signals=0,
                unknown_outcomes=0,
                win_count=0,
                loss_count=0,
                breakeven_count=0,
                avg_pnl_pct=None,
                median_pnl_pct=None,
                max_drawdown_pct=None,
                unknown_outcome_rate="1.0",
                metadata_backed_rate="0.0",
                liquidity_backed_rate="0.0",
                quality_weighted_score=0,
                limitations=["no_records_in_window"],
            )

        # Check required features
        first_features = {k: v for k, v in records[0].items() if k not in OUTCOME_KEYS}
        missing_required = [
            f for f in strategy_def.required_features if f not in first_features
        ]
        if missing_required:
            return StrategyWindowEvaluation(
                evaluation_id=evaluation_id,
                dataset_id=dataset_id,
                window_id=window_id,
                window_type=window_type,
                strategy_id=strategy_def.strategy_id,
                records_evaluated=len(records),
                signals_generated=0,
                accepted_signals=0,
                rejected_signals=0,
                unknown_outcomes=0,
                win_count=0,
                loss_count=0,
                breakeven_count=0,
                avg_pnl_pct=None,
                median_pnl_pct=None,
                max_drawdown_pct=None,
                unknown_outcome_rate="1.0",
                metadata_backed_rate="0.0",
                liquidity_backed_rate="0.0",
                quality_weighted_score=0,
                limitations=[f"insufficient_data: required features missing: {missing_required}"],
            )

        evaluator = STRATEGY_EVALUATORS.get(strategy_def.strategy_name)

        accepted_signals = 0
        rejected_signals = 0
        signals_generated = 0
        win_count = 0
        loss_count = 0
        breakeven_count = 0
        unknown_outcomes = 0
        pnl_values: List[Decimal] = []
        metadata_backed = 0
        liquidity_backed = 0
        has_future_leakage = False
        has_unsupported_batch = False
        has_xahau_context = False

        for record in records:
            features = {k: v for k, v in record.items() if k not in OUTCOME_KEYS}
            outcome = record.get("outcome") or record.get("paper_outcome")
            pnl_raw = record.get("pnl_pct") or record.get("paper_pnl_pct")

            if record.get("future_leakage"):
                has_future_leakage = True
            if record.get("unsupported_batch_context"):
                has_unsupported_batch = True
            if record.get("xahau_hook_context") or record.get("xahau_context"):
                has_xahau_context = True

            if evaluator:
                sig, _reason, _ev = evaluator(features)
            else:
                sig = "unknown"

            if sig == "accept":
                accepted_signals += 1
                signals_generated += 1
            elif sig == "reject":
                rejected_signals += 1
                signals_generated += 1

            if outcome is None:
                unknown_outcomes += 1
            elif str(outcome).lower() in ("win", "1", "true"):
                win_count += 1
            elif str(outcome).lower() in ("loss", "-1", "false", "0"):
                loss_count += 1
            elif str(outcome).lower() in ("breakeven", "be", "0.0", "0"):
                breakeven_count += 1
            else:
                unknown_outcomes += 1

            pnl_dec = _to_decimal(pnl_raw)
            if pnl_dec is not None:
                pnl_values.append(pnl_dec)

            if features.get("has_metadata") or features.get("metadata_completeness_score"):
                metadata_backed += 1
            if features.get("liquidity_score") or features.get("best_bid"):
                liquidity_backed += 1

        n = len(records)
        unknown_outcome_rate = Decimal(str(unknown_outcomes)) / Decimal(str(max(n, 1)))
        metadata_backed_rate = Decimal(str(metadata_backed)) / Decimal(str(max(n, 1)))
        liquidity_backed_rate = Decimal(str(liquidity_backed)) / Decimal(str(max(n, 1)))

        avg_pnl: Optional[str] = None
        median_pnl: Optional[str] = None
        max_drawdown: Optional[str] = None
        if pnl_values:
            pnl_floats = [float(v) for v in pnl_values]
            avg_pnl = str(Decimal(str(statistics.mean(pnl_floats))).quantize(Decimal("0.0001")))
            median_pnl = str(Decimal(str(statistics.median(pnl_floats))).quantize(Decimal("0.0001")))
            min_pnl = min(pnl_floats)
            max_drawdown = str(Decimal(str(min_pnl)).quantize(Decimal("0.0001")))

        # Quality scoring
        score = 100
        unknown_penalty = min(int(float(unknown_outcome_rate) * n) * 2, 20)
        score -= unknown_penalty

        meta_rate_f = float(metadata_backed_rate)
        if meta_rate_f < 0.7:
            deficit_pct = (0.7 - meta_rate_f) * 100
            score -= int(deficit_pct / 10) * 5

        liq_rate_f = float(liquidity_backed_rate)
        if liq_rate_f < 0.5:
            deficit_pct = (0.5 - liq_rate_f) * 100
            score -= int(deficit_pct / 10) * 5

        if signals_generated < 10:
            score -= 20
            limitations.append("small_sample: fewer than 10 signals generated")

        if dataset_quality_score < 60:
            score -= 15
            limitations.append(f"low_dataset_quality: dataset_quality_score={dataset_quality_score}")

        if has_future_leakage:
            score = min(score, 0)
            limitations.append("future_leakage_detected: quality capped at critical")

        if has_unsupported_batch:
            score -= 10
            limitations.append("unsupported_batch_context_in_records")

        if has_xahau_context:
            score -= 10
            limitations.append("xahau_hook_context_in_records: no confidence improvement")

        score = max(0, score)

        return StrategyWindowEvaluation(
            evaluation_id=evaluation_id,
            dataset_id=dataset_id,
            window_id=window_id,
            window_type=window_type,
            strategy_id=strategy_def.strategy_id,
            records_evaluated=n,
            signals_generated=signals_generated,
            accepted_signals=accepted_signals,
            rejected_signals=rejected_signals,
            unknown_outcomes=unknown_outcomes,
            win_count=win_count,
            loss_count=loss_count,
            breakeven_count=breakeven_count,
            avg_pnl_pct=avg_pnl,
            median_pnl_pct=median_pnl,
            max_drawdown_pct=max_drawdown,
            unknown_outcome_rate=str(unknown_outcome_rate.quantize(Decimal("0.0001"))),
            metadata_backed_rate=str(metadata_backed_rate.quantize(Decimal("0.0001"))),
            liquidity_backed_rate=str(liquidity_backed_rate.quantize(Decimal("0.0001"))),
            quality_weighted_score=score,
            limitations=limitations,
        )
