from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class StrategyEvaluation:
    evaluation_id: str
    strategy_id: str
    candidate_id: str
    would_enter: bool
    would_reject: bool
    would_hold: bool
    would_exit: bool
    reason: str
    evidence: List[str]
    risk_flags: List[str]
    confidence: str
    protocol_feature_context: List[str]
    prohibited_live_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "strategy_id": self.strategy_id,
            "candidate_id": self.candidate_id,
            "decision": {
                "would_enter": self.would_enter,
                "would_reject": self.would_reject,
                "would_hold": self.would_hold,
                "would_exit": self.would_exit
            },
            "reason": self.reason,
            "evidence": self.evidence,
            "risk_flags": self.risk_flags,
            "confidence": self.confidence,
            "protocol_feature_context": self.protocol_feature_context,
            "prohibited_live_action": self.prohibited_live_action
        }

@dataclass(frozen=True, slots=True)
class StrategyBacktestResult:
    result_id: str
    strategy_id: str
    total_candidates: int
    hypothetical_entries: int
    hypothetical_rejections: int
    paper_wins: int
    paper_losses: int
    paper_breakevens: int
    unknown_outcomes: int
    win_rate: Optional[float]
    loss_rate: Optional[float]
    unknown_outcome_rate: float
    avg_win_pct: Optional[float]
    avg_loss_pct: Optional[float]
    max_drawdown_paper: Optional[float]
    average_holding_time: Optional[float]
    rejected_winner_count: int
    false_positive_count: int
    metadata_backed_success_rate: Optional[float]
    offer_only_failure_rate: Optional[float]
    amm_backed_success_rate: Optional[float]
    trustline_backed_success_rate: Optional[float]
    protocol_feature_notes: List[str]
    risk_adjusted_score: float
    confidence: str
    limitations: List[str]
    prohibited_live_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "strategy_id": self.strategy_id,
            "total_candidates": self.total_candidates,
            "hypothetical_entries": self.hypothetical_entries,
            "hypothetical_rejections": self.hypothetical_rejections,
            "paper_wins": self.paper_wins,
            "paper_losses": self.paper_losses,
            "paper_breakevens": self.paper_breakevens,
            "unknown_outcomes": self.unknown_outcomes,
            "win_rate": self.win_rate,
            "loss_rate": self.loss_rate,
            "unknown_outcome_rate": self.unknown_outcome_rate,
            "avg_win_pct": self.avg_win_pct,
            "avg_loss_pct": self.avg_loss_pct,
            "max_drawdown_paper": self.max_drawdown_paper,
            "average_holding_time": self.average_holding_time,
            "rejected_winner_count": self.rejected_winner_count,
            "false_positive_count": self.false_positive_count,
            "metadata_backed_success_rate": self.metadata_backed_success_rate,
            "offer_only_failure_rate": self.offer_only_failure_rate,
            "amm_backed_success_rate": self.amm_backed_success_rate,
            "trustline_backed_success_rate": self.trustline_backed_success_rate,
            "protocol_feature_notes": self.protocol_feature_notes,
            "risk_adjusted_score": self.risk_adjusted_score,
            "confidence": self.confidence,
            "limitations": self.limitations,
            "prohibited_live_action": self.prohibited_live_action
        }

@dataclass(frozen=True, slots=True)
class StrategyTournamentResult:
    tournament_id: str
    ranked_strategies: List[Dict[str, Any]]
    winner_strategy_id: Optional[str]
    strongest_conditions: List[str]
    weakest_conditions: List[str]
    repeated_failures: List[str]
    protocol_feature_opportunities: List[str]
    human_review_required: bool = True
    prohibited_auto_action: str = "Live trading, parameter tuning, self-mutation"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tournament_id": self.tournament_id,
            "ranked_strategies": self.ranked_strategies,
            "winner_strategy_id": self.winner_strategy_id,
            "strongest_conditions": self.strongest_conditions,
            "weakest_conditions": self.weakest_conditions,
            "repeated_failures": self.repeated_failures,
            "protocol_feature_opportunities": self.protocol_feature_opportunities,
            "human_review_required": self.human_review_required,
            "prohibited_auto_action": self.prohibited_auto_action
        }
