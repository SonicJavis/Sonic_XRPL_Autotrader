from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class IntelligenceVerdict(str, Enum):
    WATCH = "WATCH"
    AVOID = "AVOID"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PAPER_ONLY_CANDIDATE = "PAPER_ONLY_CANDIDATE"


@dataclass(frozen=True)
class LaunchEvidenceSummary:
    launch_observed: bool
    observed_at: str
    stale: bool
    stale_reason: str


@dataclass(frozen=True)
class SourceProvenanceSummary:
    source_type: str
    source_url: str
    source_hash: str
    source_backed: bool
    source_trust_known: bool
    synthetic: bool


@dataclass(frozen=True)
class IssuerRiskSummary:
    issuer: str
    dev_hold_ratio: float | None
    issuer_hold_ratio: float | None
    issuer_concentration_risk: bool


@dataclass(frozen=True)
class HolderRiskSummary:
    holder_count: int | None
    top_holder_ratio: float | None
    holder_concentration_risk: bool
    holder_evidence_missing: bool


@dataclass(frozen=True)
class LiquidityEvidenceSummary:
    liquidity_usd: float | None
    thin_liquidity: bool
    liquidity_evidence_missing: bool


@dataclass(frozen=True)
class TokenControlRiskSummary:
    freeze_enabled: bool | None
    clawback_enabled: bool | None
    trustline_risk: bool


@dataclass(frozen=True)
class MetadataQualitySummary:
    metadata_status: str
    metadata_mismatch: bool


@dataclass(frozen=True)
class IntelligenceInput:
    candidate_id: str
    issuer: str
    currency: str
    symbol: str
    tx_hash: str
    ledger_index: int | None
    observed_at: str
    source_type: str
    source_url: str
    source_hash: str
    synthetic: bool = False
    source_backed: bool = True
    source_trust_known: bool = True
    metadata_status: str = "missing"
    metadata_mismatch: bool = False
    launch_quality: str = "unknown"
    holder_count: int | None = None
    top_holder_ratio: float | None = None
    dev_hold_ratio: float | None = None
    issuer_hold_ratio: float | None = None
    liquidity_usd: float | None = None
    freeze_enabled: bool | None = None
    clawback_enabled: bool | None = None
    same_symbol_different_issuer: bool = False
    source_conflict: bool = False
    stale_hours: int | None = None
    malformed_source_record: bool = False
    limitations: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RiskFeatureSummary:
    issuer_concentration_risk: bool
    holder_concentration_risk: bool
    missing_holder_evidence: bool
    missing_liquidity_evidence: bool
    thin_liquidity: bool
    freeze_clawback_risk: bool
    metadata_mismatch_risk: bool
    same_symbol_different_issuer: bool
    source_conflict: bool
    unsupported_capability_evidence: bool


@dataclass(frozen=True)
class ConfidenceBand:
    score: int
    band: str


@dataclass(frozen=True)
class FirstLedgerIntelligenceResult:
    candidate_id: str
    issuer: str
    currency: str
    symbol: str
    verdict: IntelligenceVerdict
    confidence: ConfidenceBand
    source_provenance: SourceProvenanceSummary
    launch_evidence: LaunchEvidenceSummary
    issuer_risk: IssuerRiskSummary
    holder_risk: HolderRiskSummary
    liquidity_evidence: LiquidityEvidenceSummary
    token_control_risk: TokenControlRiskSummary
    metadata_quality: MetadataQualitySummary
    risk_features: RiskFeatureSummary
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    fail_closed_reasons: tuple[str, ...]
    paper_only: bool = True
    review_only: bool = True
    live_execution_allowed: bool = False
