from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass(frozen=True)
class DatasetStrategyDefinition:
    strategy_id: str
    strategy_name: str
    strategy_version: str
    strategy_family: str  # amm_seeded | trustline_spike | offer_noise_filter | metadata_quality | liquidity_guard | baseline | unknown
    description: str
    required_features: List[str] = field(default_factory=list)
    prohibited_live_action: str = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_version": self.strategy_version,
            "strategy_family": self.strategy_family,
            "description": self.description,
            "required_features": list(self.required_features),
            "prohibited_live_action": self.prohibited_live_action,
        }


@dataclass(frozen=True)
class StrategyWindowEvaluation:
    evaluation_id: str
    dataset_id: str
    window_id: str
    window_type: str  # train | validation | test | replay | holdout
    strategy_id: str
    records_evaluated: int
    signals_generated: int
    accepted_signals: int
    rejected_signals: int
    unknown_outcomes: int
    win_count: int
    loss_count: int
    breakeven_count: int
    avg_pnl_pct: Optional[str]
    median_pnl_pct: Optional[str]
    max_drawdown_pct: Optional[str]
    unknown_outcome_rate: str
    metadata_backed_rate: str
    liquidity_backed_rate: str
    quality_weighted_score: int
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "dataset_id": self.dataset_id,
            "window_id": self.window_id,
            "window_type": self.window_type,
            "strategy_id": self.strategy_id,
            "records_evaluated": self.records_evaluated,
            "signals_generated": self.signals_generated,
            "accepted_signals": self.accepted_signals,
            "rejected_signals": self.rejected_signals,
            "unknown_outcomes": self.unknown_outcomes,
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "breakeven_count": self.breakeven_count,
            "avg_pnl_pct": self.avg_pnl_pct,
            "median_pnl_pct": self.median_pnl_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "unknown_outcome_rate": self.unknown_outcome_rate,
            "metadata_backed_rate": self.metadata_backed_rate,
            "liquidity_backed_rate": self.liquidity_backed_rate,
            "quality_weighted_score": self.quality_weighted_score,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class StrategyGeneralizationScore:
    generalization_id: str
    dataset_id: str
    strategy_id: str
    train_score: int
    validation_score: int
    test_score: int
    holdout_score: Optional[int]
    train_to_test_degradation_pct: str
    validation_to_test_degradation_pct: str
    robustness_score: int
    overfitting_score: int
    confidence_band: str  # low | medium | high
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generalization_id": self.generalization_id,
            "dataset_id": self.dataset_id,
            "strategy_id": self.strategy_id,
            "train_score": self.train_score,
            "validation_score": self.validation_score,
            "test_score": self.test_score,
            "holdout_score": self.holdout_score,
            "train_to_test_degradation_pct": self.train_to_test_degradation_pct,
            "validation_to_test_degradation_pct": self.validation_to_test_degradation_pct,
            "robustness_score": self.robustness_score,
            "overfitting_score": self.overfitting_score,
            "confidence_band": self.confidence_band,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class OverfittingWarning:
    warning_id: str
    dataset_id: str
    strategy_id: str
    warning_type: str
    severity: str  # info | caution | warning | critical
    evidence: List[str] = field(default_factory=list)
    recommended_human_action: str = ""
    prohibited_auto_action: str = "Automated live trading, parameter mutation, model self-modification"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "warning_id": self.warning_id,
            "dataset_id": self.dataset_id,
            "strategy_id": self.strategy_id,
            "warning_type": self.warning_type,
            "severity": self.severity,
            "evidence": list(self.evidence),
            "recommended_human_action": self.recommended_human_action,
            "prohibited_auto_action": self.prohibited_auto_action,
        }


@dataclass(frozen=True)
class StrategyTournamentResult:
    tournament_id: str
    dataset_id: str
    strategy_id: str
    rank: int
    overall_score: int
    generalization_score: int
    robustness_score: int
    risk_adjusted_score: int
    overfitting_score: int
    promotion_status: str  # promote_to_more_paper_tests | keep_under_review | reject_for_now | insufficient_data
    promotion_reason: str
    required_human_action: str
    prohibited_live_action: str = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tournament_id": self.tournament_id,
            "dataset_id": self.dataset_id,
            "strategy_id": self.strategy_id,
            "rank": self.rank,
            "overall_score": self.overall_score,
            "generalization_score": self.generalization_score,
            "robustness_score": self.robustness_score,
            "risk_adjusted_score": self.risk_adjusted_score,
            "overfitting_score": self.overfitting_score,
            "promotion_status": self.promotion_status,
            "promotion_reason": self.promotion_reason,
            "required_human_action": self.required_human_action,
            "prohibited_live_action": self.prohibited_live_action,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class DatasetTournamentSummary:
    summary_id: str
    dataset_id: str
    dataset_quality_score: int
    strategies_evaluated: int
    windows_evaluated: int
    best_strategy_id: Optional[str]
    worst_strategy_id: Optional[str]
    critical_warning_count: int
    recommendation_counts: Dict[str, int] = field(default_factory=dict)
    live_trading_readiness: str = "0/100"
    prohibited_live_action: str = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "dataset_id": self.dataset_id,
            "dataset_quality_score": self.dataset_quality_score,
            "strategies_evaluated": self.strategies_evaluated,
            "windows_evaluated": self.windows_evaluated,
            "best_strategy_id": self.best_strategy_id,
            "worst_strategy_id": self.worst_strategy_id,
            "critical_warning_count": self.critical_warning_count,
            "recommendation_counts": dict(self.recommendation_counts),
            "live_trading_readiness": self.live_trading_readiness,
            "prohibited_live_action": self.prohibited_live_action,
            "limitations": list(self.limitations),
        }
