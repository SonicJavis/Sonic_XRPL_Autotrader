from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .loaders import DatasetLoader
from .models import (
    DatasetStrategyDefinition,
    DatasetTournamentSummary,
    StrategyTournamentResult,
    StrategyWindowEvaluation,
)
from .overfitting import OverfittingDetector
from .scoring import ScoringEngine
from .strategy_registry import STRATEGY_REGISTRY
from .window_evaluator import WindowEvaluator

PROHIBITED_LIVE = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."
WINDOW_TYPES = ["train", "validation", "test", "replay", "holdout"]


def _tournament_id(dataset_id: str, strategy_id: str) -> str:
    raw = "|".join(sorted([dataset_id, strategy_id, "tournament_result"]))
    return hashlib.sha256(raw.encode()).hexdigest()


def _summary_id(dataset_id: str, ts: str) -> str:
    raw = "|".join(sorted([dataset_id, ts, "tournament_summary"]))
    return hashlib.sha256(raw.encode()).hexdigest()


def _determine_promotion(
    window_evals: Dict[str, StrategyWindowEvaluation],
    gen_score: Any,
    overfitting_warnings: List[Any],
    options: dict,
) -> Tuple[str, str]:
    min_signals = options.get("min_signal_count", 10)
    max_deg = options.get("max_train_test_degradation", 0.35)
    include_holdout = options.get("include_holdout", False)

    test_eval = window_evals.get("test")
    test_score = test_eval.quality_weighted_score if test_eval else 0
    test_signals = test_eval.signals_generated if test_eval else 0

    critical_warnings = [w for w in overfitting_warnings if w.severity == "critical"]
    overfitting_score = gen_score.overfitting_score

    try:
        deg_f = float(Decimal(gen_score.train_to_test_degradation_pct)) / 100.0
    except Exception:
        deg_f = 0.0

    total_signals = sum(
        ev.signals_generated for ev in window_evals.values()
    )

    quality_scores = [ev.quality_weighted_score for ev in window_evals.values()]
    avg_quality = sum(quality_scores) / max(len(quality_scores), 1)

    if total_signals < 5 or avg_quality < 30:
        return (
            "insufficient_data",
            f"Insufficient data: total_signals={total_signals}, avg_quality={avg_quality:.0f}",
        )

    if critical_warnings or test_score < 20 or overfitting_score > 70:
        reasons = []
        if critical_warnings:
            reasons.append(f"{len(critical_warnings)} critical warnings")
        if test_score < 20:
            reasons.append(f"test_score={test_score} below 20")
        if overfitting_score > 70:
            reasons.append(f"overfitting_score={overfitting_score} above 70")
        return ("reject_for_now", "; ".join(reasons))

    if (
        not critical_warnings
        and test_score > 50
        and overfitting_score < 40
        and test_signals >= min_signals
        and avg_quality >= 60
        and deg_f <= max_deg
    ):
        reason = (
            f"test_score={test_score}, overfitting_score={overfitting_score}, "
            f"test_signals={test_signals}, avg_quality={avg_quality:.0f}"
        )
        return ("promote_to_more_paper_tests", reason)

    return (
        "keep_under_review",
        f"Mixed results: test_score={test_score}, overfitting_score={overfitting_score}",
    )


class TournamentRunner:
    def __init__(self) -> None:
        self._loader = DatasetLoader()
        self._evaluator = WindowEvaluator()
        self._scorer = ScoringEngine()
        self._detector = OverfittingDetector()

    def run(
        self,
        dataset_folder: Path,
        output_dir: Path,
        options: dict,
    ) -> DatasetTournamentSummary:
        dataset = self._loader.load_dataset_folder(dataset_folder)
        manifest = dataset.get("manifest", {})
        quality_report = dataset.get("quality_report", {})
        records_by_window = dataset.get("records_by_window", {})

        dataset_id = manifest.get("dataset_id", "unknown_dataset")
        dataset_quality_score = quality_report.get("quality_score", 50)

        all_results: List[StrategyTournamentResult] = []
        all_window_evals: List[StrategyWindowEvaluation] = []
        all_gen_scores = []
        all_overfitting_warnings = []

        include_holdout = options.get("include_holdout", False)
        active_windows = WINDOW_TYPES if include_holdout else [w for w in WINDOW_TYPES if w != "holdout"]

        for strat_name, strat_def in STRATEGY_REGISTRY.items():
            window_evals: Dict[str, StrategyWindowEvaluation] = {}

            for wtype in active_windows:
                records = records_by_window.get(wtype, [])
                window_id = hashlib.sha256(f"{dataset_id}|{wtype}".encode()).hexdigest()
                eval_result = self._evaluator.evaluate(
                    strat_def, records, window_id, wtype, dataset_id, dataset_quality_score
                )
                window_evals[wtype] = eval_result
                all_window_evals.append(eval_result)

            gen_score = self._scorer.compute_generalization(
                strat_def.strategy_id, dataset_id, window_evals
            )
            all_gen_scores.append(gen_score)

            ov_warnings = self._detector.detect(
                strat_def.strategy_id, dataset_id, window_evals, gen_score, dataset_quality_score
            )
            all_overfitting_warnings.extend(ov_warnings)

            promotion_status, promotion_reason = _determine_promotion(
                window_evals, gen_score, ov_warnings, options
            )

            quality_weighted_avg = sum(
                ev.quality_weighted_score for ev in window_evals.values()
            ) / max(len(window_evals), 1)

            overfitting_score = gen_score.overfitting_score
            test_score = window_evals.get("test", StrategyWindowEvaluation(
                evaluation_id="", dataset_id="", window_id="", window_type="test",
                strategy_id="", records_evaluated=0, signals_generated=0,
                accepted_signals=0, rejected_signals=0, unknown_outcomes=0,
                win_count=0, loss_count=0, breakeven_count=0,
                avg_pnl_pct=None, median_pnl_pct=None, max_drawdown_pct=None,
                unknown_outcome_rate="1.0", metadata_backed_rate="0.0",
                liquidity_backed_rate="0.0", quality_weighted_score=0,
            )).quality_weighted_score

            overall_score = int(
                test_score * 0.40
                + gen_score.robustness_score * 0.25
                + quality_weighted_avg * 0.20
                + (100 - overfitting_score) * 0.15
            )
            overall_score = max(0, min(100, overall_score))

            risk_adjusted = overall_score - (overfitting_score * 0.3)
            risk_adjusted_score = max(0, min(100, int(risk_adjusted)))

            tournament_result = StrategyTournamentResult(
                tournament_id=_tournament_id(dataset_id, strat_def.strategy_id),
                dataset_id=dataset_id,
                strategy_id=strat_def.strategy_id,
                rank=0,
                overall_score=overall_score,
                generalization_score=gen_score.test_score,
                robustness_score=gen_score.robustness_score,
                risk_adjusted_score=risk_adjusted_score,
                overfitting_score=overfitting_score,
                promotion_status=promotion_status,
                promotion_reason=promotion_reason,
                required_human_action="Human review required before any further testing.",
                prohibited_live_action=PROHIBITED_LIVE,
                limitations=gen_score.limitations,
            )
            all_results.append(tournament_result)

        all_results.sort(key=lambda r: r.overall_score, reverse=True)
        ranked_results = []
        for rank, result in enumerate(all_results, start=1):
            from dataclasses import replace
            ranked_results.append(replace(result, rank=rank))

        recommendation_counts: Dict[str, int] = {}
        for r in ranked_results:
            recommendation_counts[r.promotion_status] = recommendation_counts.get(r.promotion_status, 0) + 1

        critical_warning_count = sum(
            1 for w in all_overfitting_warnings if w.severity == "critical"
        )

        best_id = ranked_results[0].strategy_id if ranked_results else None
        worst_id = ranked_results[-1].strategy_id if ranked_results else None

        ts = datetime.now(timezone.utc).isoformat()
        summary = DatasetTournamentSummary(
            summary_id=_summary_id(dataset_id, ts),
            dataset_id=dataset_id,
            dataset_quality_score=dataset_quality_score,
            strategies_evaluated=len(ranked_results),
            windows_evaluated=len(all_window_evals),
            best_strategy_id=best_id,
            worst_strategy_id=worst_id,
            critical_warning_count=critical_warning_count,
            recommendation_counts=recommendation_counts,
            live_trading_readiness="0/100",
            prohibited_live_action=PROHIBITED_LIVE,
            limitations=["paper_only_evaluation", "no_live_data_used"],
        )

        if not options.get("dry_run", False):
            from .report_writer import ReportWriter
            writer = ReportWriter()
            writer.write_all(
                output_dir=output_dir,
                strategy_defs=list(STRATEGY_REGISTRY.values()),
                window_evals=all_window_evals,
                gen_scores=all_gen_scores,
                overfitting_warnings=all_overfitting_warnings,
                tournament_results=ranked_results,
                summary=summary,
            )

        return summary
