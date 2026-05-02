from __future__ import annotations
import hashlib
import statistics
from decimal import Decimal
from typing import Dict, List, Optional

from .models import StrategyGeneralizationScore, StrategyWindowEvaluation


def _gen_id(strategy_id: str, dataset_id: str) -> str:
    raw = "|".join(sorted([strategy_id, dataset_id, "generalization"]))
    return hashlib.sha256(raw.encode()).hexdigest()


class ScoringEngine:
    def compute_generalization(
        self,
        strategy_id: str,
        dataset_id: str,
        window_evals: Dict[str, StrategyWindowEvaluation],
    ) -> StrategyGeneralizationScore:
        generalization_id = _gen_id(strategy_id, dataset_id)
        limitations: List[str] = []

        train_eval = window_evals.get("train")
        validation_eval = window_evals.get("validation")
        test_eval = window_evals.get("test")
        replay_eval = window_evals.get("replay")
        holdout_eval = window_evals.get("holdout")

        train_score = train_eval.quality_weighted_score if train_eval else 0
        validation_score = validation_eval.quality_weighted_score if validation_eval else 0
        test_score = test_eval.quality_weighted_score if test_eval else 0
        holdout_score: Optional[int] = holdout_eval.quality_weighted_score if holdout_eval else None

        train_denom = max(train_score, 1)
        test_denom = max(test_score, 1)
        validation_denom = max(validation_score, 1)

        train_to_test_deg = Decimal(str((train_score - test_score))) / Decimal(str(train_denom)) * Decimal("100")
        val_to_test_deg = Decimal(str((validation_score - test_score))) / Decimal(str(validation_denom)) * Decimal("100")

        available_scores: List[int] = []
        for ev in [train_eval, validation_eval, test_eval, replay_eval]:
            if ev is not None:
                available_scores.append(ev.quality_weighted_score)
        if holdout_eval is not None:
            available_scores.append(holdout_eval.quality_weighted_score)

        if available_scores:
            mean_score = statistics.mean(available_scores)
            if len(available_scores) > 1:
                variance = statistics.variance(available_scores)
                variance_penalty = min(int(variance / 100), 20)
            else:
                variance_penalty = 10
                limitations.append("single_window_only: variance unknown")
            robustness_raw = int(mean_score) - variance_penalty
        else:
            robustness_raw = 0
            limitations.append("no_window_evaluations_available")

        robustness_score = max(0, min(100, robustness_raw))

        deg_f = float(train_to_test_deg)
        if deg_f > 50:
            overfitting_score = 90
        elif deg_f > 35:
            overfitting_score = 70
        elif deg_f > 20:
            overfitting_score = 50
        elif deg_f > 10:
            overfitting_score = 30
        else:
            overfitting_score = max(0, int(deg_f))

        if robustness_score > 70 and overfitting_score < 40:
            confidence_band = "high"
        elif robustness_score >= 40:
            confidence_band = "medium"
        else:
            confidence_band = "low"

        if not train_eval:
            limitations.append("train_window_missing")
        if not validation_eval:
            limitations.append("validation_window_missing")
        if not test_eval:
            limitations.append("test_window_missing")

        return StrategyGeneralizationScore(
            generalization_id=generalization_id,
            dataset_id=dataset_id,
            strategy_id=strategy_id,
            train_score=train_score,
            validation_score=validation_score,
            test_score=test_score,
            holdout_score=holdout_score,
            train_to_test_degradation_pct=str(train_to_test_deg.quantize(Decimal("0.01"))),
            validation_to_test_degradation_pct=str(val_to_test_deg.quantize(Decimal("0.01"))),
            robustness_score=robustness_score,
            overfitting_score=overfitting_score,
            confidence_band=confidence_band,
            limitations=limitations,
        )
