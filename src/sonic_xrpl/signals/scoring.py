"""Conservative deterministic scoring for FirstLedger candidate signals."""

from __future__ import annotations

from typing import Any

from sonic_xrpl.market.models import MarketSnapshot
from sonic_xrpl.protocol.capability_matrix import is_capability_available
from sonic_xrpl.signals.models import FirstLedgerCandidateEvidence, ScoringBreakdown

CRITICAL_LIMITATION_PREFIXES = (
    "explicit_risk:",
    "issuer_freeze_detected",
    "trustline_deep_freeze_detected",
    "clawback_risk_detected",
)


def has_critical_limitation(candidate: FirstLedgerCandidateEvidence) -> bool:
    """Return True if evidence includes an explicit avoid-level risk."""
    return any(
        limitation.startswith(CRITICAL_LIMITATION_PREFIXES)
        or limitation in {"critical_risk", "known_scam_source", "malicious_source_flag"}
        for limitation in candidate.limitations
    )


def _snapshot_matches_candidate(snapshot: MarketSnapshot | None, candidate: FirstLedgerCandidateEvidence) -> bool:
    if snapshot is None:
        return False
    issuer = candidate.issuer
    currency = candidate.currency
    return any(asset.issuer == issuer and asset.currency == currency for asset in snapshot.assets) or any(
        line.issuer == issuer and line.currency == currency for line in snapshot.trustlines
    )


def score_candidate(candidate: FirstLedgerCandidateEvidence, market_snapshot: MarketSnapshot | None = None) -> ScoringBreakdown:
    """Score evidence quality and risk conservatively.

    Missing data never receives positive credit. Unknowns and explicit risks are
    penalized, and liquidity is only credited when a market snapshot is supplied.
    """
    provenance_fields = [candidate.source_url, candidate.source_hash, candidate.source_type]
    provenance_score = min(20, sum(7 for value in provenance_fields if value))
    if candidate.synthetic:
        provenance_score = min(provenance_score, 8)

    metadata_score = 20 if candidate.metadata_status == "validated" else (8 if candidate.metadata_status == "present_unvalidated" else 0)
    issuer_risk_score = 0 if not candidate.issuer or has_critical_limitation(candidate) else 15
    trustline_risk_score = 0 if any("freeze" in lim or "clawback" in lim for lim in candidate.limitations) else 10

    snapshot_match = _snapshot_matches_candidate(market_snapshot, candidate)
    market_snapshot_score = 15 if snapshot_match else 0
    liquidity_evidence_score = 5 if snapshot_match else 0

    missing_penalty = len(candidate.raw_fields_missing) * 12
    unknown_penalty = missing_penalty
    if candidate.metadata_status != "validated":
        unknown_penalty += 12
    if market_snapshot is None:
        unknown_penalty += 8
    if candidate.synthetic:
        unknown_penalty += 20
    if has_critical_limitation(candidate):
        unknown_penalty += 35
    if not is_capability_available("TrustSet"):
        unknown_penalty += 5

    positive = provenance_score + metadata_score + issuer_risk_score + trustline_risk_score + market_snapshot_score + liquidity_evidence_score
    final_score = max(0, min(100, positive - unknown_penalty))
    return ScoringBreakdown(
        provenance_score=provenance_score,
        metadata_score=metadata_score,
        issuer_risk_score=issuer_risk_score,
        trustline_risk_score=trustline_risk_score,
        market_snapshot_score=market_snapshot_score,
        liquidity_evidence_score=liquidity_evidence_score,
        unknown_penalty=unknown_penalty,
        final_score=final_score,
    )
