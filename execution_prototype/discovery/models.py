from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class RawDiscoveryEvent:
    event_id: str
    event_type: str # trustline_created | amm_created | issuer_activity | offer_activity_low_confidence
    issuer: str
    currency_code: str
    ledger_index: int
    tx_hash: str
    validated: bool
    metadata_present: bool
    observed_at: str
    limitations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "issuer": self.issuer,
            "currency_code": self.currency_code,
            "ledger_index": self.ledger_index,
            "tx_hash": self.tx_hash,
            "validated": self.validated,
            "metadata_present": self.metadata_present,
            "observed_at": self.observed_at,
            "limitations": self.limitations
        }

@dataclass(frozen=True, slots=True)
class MemeCandidate:
    candidate_id: str
    issuer: str
    currency_code: str
    first_seen_ledger: int
    evidence_event_ids: List[str]
    signal_summary: str
    confidence: str # low | medium | high
    risk_flags: List[str]
    score: int
    score_band: str # ignore | watch | review | high_attention
    human_review_required: bool = True
    prohibited_auto_action: str = "Do not treat this advisory signal as a buy recommendation. Auto-trading is forbidden."
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "issuer": self.issuer,
            "currency_code": self.currency_code,
            "first_seen_ledger": self.first_seen_ledger,
            "evidence_event_ids": self.evidence_event_ids,
            "signal_summary": self.signal_summary,
            "confidence": self.confidence,
            "risk_flags": self.risk_flags,
            "score": self.score,
            "score_band": self.score_band,
            "human_review_required": self.human_review_required,
            "prohibited_auto_action": self.prohibited_auto_action
        }

@dataclass(frozen=True, slots=True)
class DiscoverySummary:
    schema_version: str
    generated_at: str
    total_events_processed: int
    total_candidates_found: int
    candidates_by_band: Dict[str, int]
    safety_statement: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "total_events_processed": self.total_events_processed,
            "total_candidates_found": self.total_candidates_found,
            "candidates_by_band": self.candidates_by_band,
            "safety_statement": self.safety_statement
        }
