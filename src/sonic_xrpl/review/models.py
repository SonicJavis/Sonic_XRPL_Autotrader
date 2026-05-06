from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Tuple, Optional

from sonic_xrpl.signals.models import CandidateRiskSignal, FirstLedgerCandidateEvidence, ScoringBreakdown
from sonic_xrpl.signals.evidence import stable_id

@dataclass(frozen=True)
class SignalReviewItem:
    review_id: str
    candidate_id: str
    signal_id: str
    issuer: str
    currency: str
    classification: str  # buy/watch/avoid/etc
    confidence_score: int
    risk_score: int
    decision_recommendation: str  # PAPER_REVIEW / PAPER_WATCH / PAPER_REJECT / INSUFFICIENT_EVIDENCE
    evidence_summary: str
    missing_evidence: Tuple[str, ...]
    limitations: Tuple[str, ...]
    provenance: Tuple[str, ...]
    synthetic: bool
    created_at: str
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class PaperDecision:
    decision_id: str
    review_id: str
    candidate_id: str
    signal_id: str
    generated_at: str
    decision: str  # PAPER_APPROVE / PAPER_WATCH / PAPER_REJECT / NEEDS_MORE_EVIDENCE
    reason_codes: Tuple[str, ...]
    human_review_required: bool
    limitations: Tuple[str, ...]
    live_execution_allowed: bool = False
    paper_only: bool = True


@dataclass(frozen=True)
class PaperTradeIntent:
    intent_id: str
    decision_id: str
    candidate_id: str
    issuer: str
    currency: str
    side: str  # BUY_SIMULATED / WATCH_ONLY / REJECTED
    sizing_mode: str  # FIXED_TEST_SIZE / RISK_CAPPED_TEST_SIZE / NONE
    notional_xrp: float | int | None
    max_slippage_bps: float | None
    created_from_signal_id: str
    execution_block_reason: str
    live_execution_allowed: bool = False
    requires_human_review: bool = True


@dataclass(frozen=True)
class ReviewQueue:
    queue_id: str
    items: Tuple[SignalReviewItem, ...]
    generated_at: str
    source_fixture: str
    limitations: Tuple[str, ...] = field(default_factory=tuple)

    def counts_by_classification(self) -> dict[str, int]:
        d: dict[str, int] = {}
        for it in self.items:
            d[it.classification] = d.get(it.classification, 0) + 1
        return d


@dataclass(frozen=True)
class ReviewAuditRecord:
    record_id: str
    event_type: str
    review_id: str
    decision_id: Optional[str]
    source_signal_id: str
    message: str
    timestamp: str
    safety_flags: Tuple[str, ...] = field(default_factory=tuple)
