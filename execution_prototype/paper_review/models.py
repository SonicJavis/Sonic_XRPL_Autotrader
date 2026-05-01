from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class PaperTradeHistory:
    trade_id: str
    campaign_id: str
    candidate_id: str
    issuer: str
    currency_code: str
    entry_decision_id: str
    exit_decision_id: Optional[str]
    entry_time: str
    exit_time: Optional[str]
    entry_score: int
    exit_score: Optional[int]
    entry_score_band: str
    exit_score_band: Optional[str]
    entry_reason: str
    exit_reason: Optional[str]
    risk_flags_at_entry: List[str]
    risk_flags_at_exit: List[str]
    evidence_event_ids: List[str]
    source_signal_types: List[str]
    metadata_present_at_entry: bool
    validated_ledger_evidence: bool
    amm_present: bool
    liquidity_signal_strength: str # none | weak | medium | strong
    paper_size_xrp: float
    entry_price_paper: Optional[float]
    exit_price_paper: Optional[float]
    paper_pnl_xrp: Optional[float]
    paper_pnl_pct: Optional[float]
    outcome: str # win | loss | breakeven | unknown
    mistake_tags: List[str]
    success_tags: List[str]
    improvement_notes: List[str]
    prohibited_auto_action: str = "Do not automate future entry based on this paper trade."
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "campaign_id": self.campaign_id,
            "candidate_id": self.candidate_id,
            "issuer": self.issuer,
            "currency_code": self.currency_code,
            "entry_decision_id": self.entry_decision_id,
            "exit_decision_id": self.exit_decision_id,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "entry_score": self.entry_score,
            "exit_score": self.exit_score,
            "entry_score_band": self.entry_score_band,
            "exit_score_band": self.exit_score_band,
            "entry_reason": self.entry_reason,
            "exit_reason": self.exit_reason,
            "risk_flags_at_entry": self.risk_flags_at_entry,
            "risk_flags_at_exit": self.risk_flags_at_exit,
            "evidence_event_ids": self.evidence_event_ids,
            "source_signal_types": self.source_signal_types,
            "metadata_present_at_entry": self.metadata_present_at_entry,
            "validated_ledger_evidence": self.validated_ledger_evidence,
            "amm_present": self.amm_present,
            "liquidity_signal_strength": self.liquidity_signal_strength,
            "paper_size_xrp": self.paper_size_xrp,
            "entry_price_paper": self.entry_price_paper,
            "exit_price_paper": self.exit_price_paper,
            "paper_pnl_xrp": self.paper_pnl_xrp,
            "paper_pnl_pct": self.paper_pnl_pct,
            "outcome": self.outcome,
            "mistake_tags": self.mistake_tags,
            "success_tags": self.success_tags,
            "improvement_notes": self.improvement_notes,
            "prohibited_auto_action": self.prohibited_auto_action
        }

@dataclass(frozen=True, slots=True)
class PerformanceReview:
    review_id: str
    campaign_id: str
    total_trades: int
    wins: int
    losses: int
    breakevens: int
    unknown_outcomes: int
    win_rate: Optional[float]
    avg_win_pct: Optional[float]
    avg_loss_pct: Optional[float]
    best_trade_id: Optional[str]
    worst_trade_id: Optional[str]
    best_setup_tags: List[str]
    worst_setup_tags: List[str]
    repeated_mistakes: List[str]
    strongest_setups: List[str]
    weakest_setups: List[str]
    what_worked: List[str]
    what_failed: List[str]
    improve_next_time: List[str]
    human_review_required: bool = True
    prohibited_auto_action: str = "Do not auto-adjust strategy parameters or authorize live trading based on this review."
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "campaign_id": self.campaign_id,
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "breakevens": self.breakevens,
            "unknown_outcomes": self.unknown_outcomes,
            "win_rate": self.win_rate,
            "avg_win_pct": self.avg_win_pct,
            "avg_loss_pct": self.avg_loss_pct,
            "best_trade_id": self.best_trade_id,
            "worst_trade_id": self.worst_trade_id,
            "best_setup_tags": self.best_setup_tags,
            "worst_setup_tags": self.worst_setup_tags,
            "repeated_mistakes": self.repeated_mistakes,
            "strongest_setups": self.strongest_setups,
            "weakest_setups": self.weakest_setups,
            "what_worked": self.what_worked,
            "what_failed": self.what_failed,
            "improve_next_time": self.improve_next_time,
            "human_review_required": self.human_review_required,
            "prohibited_auto_action": self.prohibited_auto_action
        }
