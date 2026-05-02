from __future__ import annotations
import hashlib
from decimal import Decimal, InvalidOperation
from typing import Dict, List

from .models import OverfittingWarning, StrategyGeneralizationScore, StrategyWindowEvaluation

PROHIBITED_AUTO = "Automated live trading, parameter mutation, model self-modification"


def _warning_id(evidence: List[str]) -> str:
    combined = "|".join(sorted(evidence))
    return hashlib.sha256(combined.encode()).hexdigest()


class OverfittingDetector:
    def detect(
        self,
        strategy_id: str,
        dataset_id: str,
        window_evals: Dict[str, StrategyWindowEvaluation],
        gen_score: StrategyGeneralizationScore,
        quality_score: int,
    ) -> List[OverfittingWarning]:
        warnings: List[OverfittingWarning] = []

        try:
            deg = Decimal(gen_score.train_to_test_degradation_pct)
        except (InvalidOperation, ValueError):
            deg = Decimal("0")

        deg_f = float(deg)
        if deg_f > 50:
            ev = [
                f"train_score={gen_score.train_score}",
                f"test_score={gen_score.test_score}",
                f"train_to_test_degradation_pct={gen_score.train_to_test_degradation_pct}",
                "degradation_exceeds_50_percent",
            ]
            warnings.append(OverfittingWarning(
                warning_id=_warning_id(ev),
                dataset_id=dataset_id,
                strategy_id=strategy_id,
                warning_type="train_test_degradation",
                severity="critical",
                evidence=ev,
                recommended_human_action="Re-examine strategy; train-test degradation is critical. Manual review required.",
                prohibited_auto_action=PROHIBITED_AUTO,
            ))
        elif deg_f > 35:
            ev = [
                f"train_score={gen_score.train_score}",
                f"test_score={gen_score.test_score}",
                f"train_to_test_degradation_pct={gen_score.train_to_test_degradation_pct}",
                "degradation_exceeds_35_percent",
            ]
            warnings.append(OverfittingWarning(
                warning_id=_warning_id(ev),
                dataset_id=dataset_id,
                strategy_id=strategy_id,
                warning_type="train_test_degradation",
                severity="warning",
                evidence=ev,
                recommended_human_action="Review strategy generalization; degradation is above 35%.",
                prohibited_auto_action=PROHIBITED_AUTO,
            ))

        val_eval = window_evals.get("validation")
        test_eval = window_evals.get("test")
        if val_eval and test_eval:
            if val_eval.quality_weighted_score > 60 and test_eval.quality_weighted_score < 40:
                ev = [
                    f"validation_score={val_eval.quality_weighted_score}",
                    f"test_score={test_eval.quality_weighted_score}",
                    "validation_strong_test_weak",
                ]
                warnings.append(OverfittingWarning(
                    warning_id=_warning_id(ev),
                    dataset_id=dataset_id,
                    strategy_id=strategy_id,
                    warning_type="validation_collapse",
                    severity="warning",
                    evidence=ev,
                    recommended_human_action="Investigate dataset split; validation strong but test weak.",
                    prohibited_auto_action=PROHIBITED_AUTO,
                ))

        holdout_eval = window_evals.get("holdout")
        if holdout_eval and holdout_eval.quality_weighted_score < 40:
            ev = [
                f"holdout_score={holdout_eval.quality_weighted_score}",
                "holdout_below_40",
            ]
            warnings.append(OverfittingWarning(
                warning_id=_warning_id(ev),
                dataset_id=dataset_id,
                strategy_id=strategy_id,
                warning_type="holdout_failure",
                severity="warning",
                evidence=ev,
                recommended_human_action="Holdout performance is poor; do not promote to further tests.",
                prohibited_auto_action=PROHIBITED_AUTO,
            ))

        for wtype, weval in window_evals.items():
            try:
                unk_rate = float(Decimal(weval.unknown_outcome_rate))
            except (InvalidOperation, ValueError):
                unk_rate = 0.0
            if unk_rate > 0.30:
                ev = [
                    f"window_type={wtype}",
                    f"unknown_outcome_rate={weval.unknown_outcome_rate}",
                    "unknown_outcome_rate_exceeds_30_percent",
                ]
                warnings.append(OverfittingWarning(
                    warning_id=_warning_id(ev),
                    dataset_id=dataset_id,
                    strategy_id=strategy_id,
                    warning_type="unknown_outcome_dependency",
                    severity="warning",
                    evidence=ev,
                    recommended_human_action=f"Window '{wtype}' has >30% unknown outcomes; results unreliable.",
                    prohibited_auto_action=PROHIBITED_AUTO,
                ))

            try:
                meta_rate = float(Decimal(weval.metadata_backed_rate))
            except (InvalidOperation, ValueError):
                meta_rate = 1.0
            if meta_rate < 0.70:
                ev = [
                    f"window_type={wtype}",
                    f"metadata_backed_rate={weval.metadata_backed_rate}",
                    "metadata_backed_rate_below_70_percent",
                ]
                warnings.append(OverfittingWarning(
                    warning_id=_warning_id(ev),
                    dataset_id=dataset_id,
                    strategy_id=strategy_id,
                    warning_type="metadata_dependency",
                    severity="caution",
                    evidence=ev,
                    recommended_human_action=f"Window '{wtype}' lacks metadata backing; add more source data.",
                    prohibited_auto_action=PROHIBITED_AUTO,
                ))

            try:
                liq_rate = float(Decimal(weval.liquidity_backed_rate))
            except (InvalidOperation, ValueError):
                liq_rate = 1.0
            if liq_rate < 0.50:
                ev = [
                    f"window_type={wtype}",
                    f"liquidity_backed_rate={weval.liquidity_backed_rate}",
                    "liquidity_backed_rate_below_50_percent",
                ]
                warnings.append(OverfittingWarning(
                    warning_id=_warning_id(ev),
                    dataset_id=dataset_id,
                    strategy_id=strategy_id,
                    warning_type="liquidity_dependency",
                    severity="caution",
                    evidence=ev,
                    recommended_human_action=f"Window '{wtype}' lacks liquidity data; enrich dataset.",
                    prohibited_auto_action=PROHIBITED_AUTO,
                ))

            if weval.signals_generated < 10:
                ev = [
                    f"window_type={wtype}",
                    f"signals_generated={weval.signals_generated}",
                    "small_sample_fewer_than_10_signals",
                ]
                warnings.append(OverfittingWarning(
                    warning_id=_warning_id(ev),
                    dataset_id=dataset_id,
                    strategy_id=strategy_id,
                    warning_type="small_sample_false_confidence",
                    severity="caution",
                    evidence=ev,
                    recommended_human_action=f"Window '{wtype}' has <10 signals; collect more data.",
                    prohibited_auto_action=PROHIBITED_AUTO,
                ))

        if quality_score < 60:
            ev = [
                f"quality_score={quality_score}",
                "quality_score_below_60",
            ]
            warnings.append(OverfittingWarning(
                warning_id=_warning_id(ev),
                dataset_id=dataset_id,
                strategy_id=strategy_id,
                warning_type="quality_sensitive",
                severity="warning",
                evidence=ev,
                recommended_human_action="Dataset quality is below 60; improve data collection before trusting results.",
                prohibited_auto_action=PROHIBITED_AUTO,
            ))

        return warnings
