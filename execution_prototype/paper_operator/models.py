from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class PaperDecision:
    decision_id: str
    candidate_id: str
    issuer: str
    currency_code: str
    action: str  # paper_enter, paper_hold, paper_exit, paper_reject
    reason: str
    confidence: str
    metadata_present: bool
    validated_ledger_evidence: bool
    risk_flags: List[str]
    score_band: str
    amm_present: bool
    liquidity_signal_strength: str
    source_signal_types: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "candidate_id": self.candidate_id,
            "issuer": self.issuer,
            "currency_code": self.currency_code,
            "action": self.action,
            "reason": self.reason,
            "confidence": self.confidence,
            "metadata_present": self.metadata_present,
            "validated_ledger_evidence": self.validated_ledger_evidence,
            "risk_flags": self.risk_flags,
            "score_band": self.score_band,
            "amm_present": self.amm_present,
            "liquidity_signal_strength": self.liquidity_signal_strength,
            "source_signal_types": self.source_signal_types,
            "timestamp": self.timestamp
        }

@dataclass(frozen=True, slots=True)
class PaperPosition:
    position_id: str
    candidate_id: str
    issuer: str
    currency_code: str
    entry_price_xrp: float
    size_xrp: float
    entry_decision_id: str
    entry_timestamp: str
    stop_loss_pct: float = 0.85
    take_profit_pct: float = 1.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_id": self.position_id,
            "candidate_id": self.candidate_id,
            "issuer": self.issuer,
            "currency_code": self.currency_code,
            "entry_price_xrp": self.entry_price_xrp,
            "size_xrp": self.size_xrp,
            "entry_decision_id": self.entry_decision_id,
            "entry_timestamp": self.entry_timestamp,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct
        }

@dataclass(frozen=True, slots=True)
class PaperLedgerState:
    campaign_id: str
    balance_xrp: float
    open_positions: Dict[str, PaperPosition]  # candidate_id -> PaperPosition
    max_positions: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "balance_xrp": self.balance_xrp,
            "open_positions": {k: v.to_dict() for k, v in self.open_positions.items()},
            "max_positions": self.max_positions
        }
