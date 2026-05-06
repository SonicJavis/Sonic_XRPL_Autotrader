"""Evidence-backed, non-executing signal contracts for FirstLedger candidates.

Phase 49 is deliberately offline and deterministic. These models are data
contracts only; they cannot authorize live execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SignalType(str, Enum):
    """Allowed non-executing candidate signal classes."""

    BUY_CANDIDATE = "BUY_CANDIDATE"
    WATCH = "WATCH"
    AVOID = "AVOID"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class FirstLedgerCandidateEvidence:
    """Source/provenance contract for a FirstLedger candidate."""

    candidate_id: str
    observed_at: str
    source_url: str
    source_type: str
    source_hash: str
    issuer: str
    currency: str
    tx_hash: str
    ledger_index: int | None
    metadata_status: str
    validation_status: str
    limitations: tuple[str, ...] = field(default_factory=tuple)
    raw_fields_present: tuple[str, ...] = field(default_factory=tuple)
    raw_fields_missing: tuple[str, ...] = field(default_factory=tuple)
    synthetic: bool = False


@dataclass(frozen=True)
class SignalEvidence:
    """Atomic evidence item used to explain a signal."""

    evidence_id: str
    source: str
    field: str
    value: Any
    confidence: int
    limitation: str
    source_backed: bool


@dataclass(frozen=True)
class ScoringBreakdown:
    """Conservative score components. Higher final score means better evidence."""

    provenance_score: int
    metadata_score: int
    issuer_risk_score: int
    trustline_risk_score: int
    market_snapshot_score: int
    liquidity_evidence_score: int
    unknown_penalty: int
    final_score: int


@dataclass(frozen=True)
class CandidateRiskSignal:
    """Deterministic advisory signal. Live execution is always forbidden."""

    signal_id: str
    candidate_id: str
    signal_type: SignalType
    confidence_score: int
    risk_score: int
    evidence_count: int
    missing_required_evidence: tuple[str, ...]
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]
    generated_at: str
    live_execution_allowed: bool = False
