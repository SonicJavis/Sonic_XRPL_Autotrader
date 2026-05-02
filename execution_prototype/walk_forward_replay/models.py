"""Phase 44: Walk-Forward Replay Models.

All dataclasses are frozen (immutable). IDs use sha256 of sorted stable JSON.
Decimals stored as strings to avoid float drift.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _stable_id(data: Dict[str, Any]) -> str:
    """Generate a deterministic 16-char hex ID from a dict."""
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class WalkForwardWindow:
    """Describes one walk-forward train/eval window pair."""

    walk_window_id: str
    dataset_id: str
    training_window_ids: List[str]
    evaluation_window_id: str
    training_ledger_range: List[int]  # [min, max]
    evaluation_ledger_range: List[int]  # [min, max]
    training_record_count: int
    evaluation_record_count: int
    chronological_order: int  # position in the rolling walk-forward sequence
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "walk_window_id": self.walk_window_id,
            "dataset_id": self.dataset_id,
            "training_window_ids": list(self.training_window_ids),
            "evaluation_window_id": self.evaluation_window_id,
            "training_ledger_range": list(self.training_ledger_range),
            "evaluation_ledger_range": list(self.evaluation_ledger_range),
            "training_record_count": self.training_record_count,
            "evaluation_record_count": self.evaluation_record_count,
            "chronological_order": self.chronological_order,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class WalkForwardEvaluation:
    """Evaluation of a single strategy on one walk-forward window."""

    evaluation_id: str
    walk_window_id: str
    dataset_id: str
    strategy_id: str
    chronological_order: int
    training_score: int
    evaluation_score: int
    score_delta: int  # evaluation_score - training_score
    unknown_outcome_rate: str  # stored as string decimal
    metadata_backed_rate: str
    liquidity_backed_rate: str
    sample_size: int
    confidence_band: str  # low | medium | high
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "walk_window_id": self.walk_window_id,
            "dataset_id": self.dataset_id,
            "strategy_id": self.strategy_id,
            "chronological_order": self.chronological_order,
            "training_score": self.training_score,
            "evaluation_score": self.evaluation_score,
            "score_delta": self.score_delta,
            "unknown_outcome_rate": self.unknown_outcome_rate,
            "metadata_backed_rate": self.metadata_backed_rate,
            "liquidity_backed_rate": self.liquidity_backed_rate,
            "sample_size": self.sample_size,
            "confidence_band": self.confidence_band,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class StrategyStabilityProfile:
    """Aggregated stability metrics for a strategy across all walk-forward windows."""

    stability_id: str
    dataset_id: str
    strategy_id: str
    windows_evaluated: int
    mean_evaluation_score: int
    median_evaluation_score: int
    score_volatility: str  # std dev as string decimal
    worst_evaluation_score: int
    best_evaluation_score: int
    degradation_count: int  # windows where score_delta < warning_threshold
    critical_degradation_count: int  # windows where score_delta < critical_threshold
    stability_score: int  # 0-100
    stability_band: str  # stable | watch | unstable | insufficient_data
    confidence_band: str  # low | medium | high
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stability_id": self.stability_id,
            "dataset_id": self.dataset_id,
            "strategy_id": self.strategy_id,
            "windows_evaluated": self.windows_evaluated,
            "mean_evaluation_score": self.mean_evaluation_score,
            "median_evaluation_score": self.median_evaluation_score,
            "score_volatility": self.score_volatility,
            "worst_evaluation_score": self.worst_evaluation_score,
            "best_evaluation_score": self.best_evaluation_score,
            "degradation_count": self.degradation_count,
            "critical_degradation_count": self.critical_degradation_count,
            "stability_score": self.stability_score,
            "stability_band": self.stability_band,
            "confidence_band": self.confidence_band,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class StrategyDegradationWarning:
    """A degradation or risk warning for a strategy detected during replay."""

    warning_id: str
    dataset_id: str
    strategy_id: str
    warning_type: str
    severity: str  # info | caution | warning | critical
    evidence: List[str] = field(default_factory=list)
    recommended_human_action: str = ""
    prohibited_auto_action: str = (
        "Automated live trading, parameter mutation, model self-modification"
    )

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
class PaperStrategyLifecycleRecommendation:
    """Lifecycle recommendation for a strategy after walk-forward evaluation."""

    recommendation_id: str
    dataset_id: str
    strategy_id: str
    lifecycle_status: str  # continue_paper_testing | increase_paper_scrutiny |
    #                         pause_paper_testing | retire_from_current_paper_pool |
    #                         insufficient_data
    reason: str
    required_human_action: str
    prohibited_live_action: str = (
        "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION. LIVE TRADING FORBIDDEN."
    )
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "dataset_id": self.dataset_id,
            "strategy_id": self.strategy_id,
            "lifecycle_status": self.lifecycle_status,
            "reason": self.reason,
            "required_human_action": self.required_human_action,
            "prohibited_live_action": self.prohibited_live_action,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class WalkForwardReplaySummary:
    """Top-level summary of a walk-forward replay run."""

    summary_id: str
    dataset_id: str
    dataset_quality_score: int
    strategies_evaluated: int
    walk_forward_windows: int
    total_evaluations: int
    stable_strategy_count: int
    watch_strategy_count: int
    unstable_strategy_count: int
    insufficient_data_count: int
    critical_warning_count: int
    lifecycle_recommendation_counts: Dict[str, int] = field(default_factory=dict)
    live_trading_readiness: str = "0/100"
    prohibited_live_action: str = (
        "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION. LIVE TRADING FORBIDDEN."
    )
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_id": self.summary_id,
            "dataset_id": self.dataset_id,
            "dataset_quality_score": self.dataset_quality_score,
            "strategies_evaluated": self.strategies_evaluated,
            "walk_forward_windows": self.walk_forward_windows,
            "total_evaluations": self.total_evaluations,
            "stable_strategy_count": self.stable_strategy_count,
            "watch_strategy_count": self.watch_strategy_count,
            "unstable_strategy_count": self.unstable_strategy_count,
            "insufficient_data_count": self.insufficient_data_count,
            "critical_warning_count": self.critical_warning_count,
            "lifecycle_recommendation_counts": dict(self.lifecycle_recommendation_counts),
            "live_trading_readiness": self.live_trading_readiness,
            "prohibited_live_action": self.prohibited_live_action,
            "limitations": list(self.limitations),
        }
