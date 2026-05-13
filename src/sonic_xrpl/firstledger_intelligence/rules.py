from __future__ import annotations

from sonic_xrpl.firstledger_intelligence.models import (
    ConfidenceBand,
    FirstLedgerIntelligenceResult,
    HolderRiskSummary,
    IntelligenceInput,
    IntelligenceVerdict,
    IssuerRiskSummary,
    LaunchEvidenceSummary,
    LiquidityEvidenceSummary,
    MetadataQualitySummary,
    SourceProvenanceSummary,
    TokenControlRiskSummary,
)
from sonic_xrpl.firstledger_intelligence.scoring import build_risk_features, confidence_band, score_confidence


_REQUIRED_FIELDS = ("issuer", "currency", "tx_hash", "ledger_index", "source_url", "observed_at")


def _missing(item: IntelligenceInput) -> tuple[str, ...]:
    missing: list[str] = []
    for field in _REQUIRED_FIELDS:
        value = getattr(item, field)
        if value in (None, ""):
            missing.append(field)
    return tuple(missing)


def _verdict(item: IntelligenceInput, score: int, missing: tuple[str, ...], fail_closed: tuple[str, ...]) -> IntelligenceVerdict:
    if fail_closed:
        return IntelligenceVerdict.INSUFFICIENT_EVIDENCE
    if missing:
        return IntelligenceVerdict.INSUFFICIENT_EVIDENCE
    if item.synthetic:
        return IntelligenceVerdict.INSUFFICIENT_EVIDENCE
    if not item.source_backed:
        return IntelligenceVerdict.INSUFFICIENT_EVIDENCE
    if item.source_conflict:
        return IntelligenceVerdict.REVIEW_REQUIRED
    if bool(item.freeze_enabled) or bool(item.clawback_enabled):
        return IntelligenceVerdict.AVOID
    if score >= 70 and item.metadata_status == "validated":
        return IntelligenceVerdict.PAPER_ONLY_CANDIDATE
    if score >= 45:
        return IntelligenceVerdict.WATCH
    return IntelligenceVerdict.REVIEW_REQUIRED


def build_intelligence_result(item: IntelligenceInput) -> FirstLedgerIntelligenceResult:
    features = build_risk_features(item)
    missing = _missing(item)

    fail_closed: list[str] = []
    if item.malformed_source_record:
        fail_closed.append("malformed_source_record")
    if item.synthetic and item.source_backed:
        fail_closed.append("synthetic_marked_source_backed_conflict")

    score = score_confidence(item, features)
    verdict = _verdict(item, score, missing, tuple(fail_closed))

    stale = bool(item.stale_hours is not None and item.stale_hours > 48)
    stale_reason = "stale_over_48h" if stale else ""

    reasons = [
        "Phase 59 output is intelligence-only and paper-only.",
        "Verdicts are review labels and never execution instructions.",
        "BUY_CANDIDATE semantics remain non-executing from Phase 49.",
    ]
    if verdict == IntelligenceVerdict.PAPER_ONLY_CANDIDATE:
        reasons.append("Source-backed evidence and conservative confidence met paper-only candidate threshold.")
    if missing:
        reasons.append("Critical evidence is missing; candidate remains insufficient evidence.")
    if item.synthetic:
        reasons.append("Synthetic evidence cannot qualify as paper-only candidate.")
    if item.source_conflict:
        reasons.append("Conflicting source evidence requires manual review.")

    return FirstLedgerIntelligenceResult(
        candidate_id=item.candidate_id,
        issuer=item.issuer,
        currency=item.currency,
        symbol=item.symbol,
        verdict=verdict,
        confidence=ConfidenceBand(score=score, band=confidence_band(score)),
        source_provenance=SourceProvenanceSummary(
            source_type=item.source_type,
            source_url=item.source_url,
            source_hash=item.source_hash,
            source_backed=item.source_backed,
            source_trust_known=item.source_trust_known,
            synthetic=item.synthetic,
        ),
        launch_evidence=LaunchEvidenceSummary(
            launch_observed=bool(item.observed_at),
            observed_at=item.observed_at,
            stale=stale,
            stale_reason=stale_reason,
        ),
        issuer_risk=IssuerRiskSummary(
            issuer=item.issuer,
            dev_hold_ratio=item.dev_hold_ratio,
            issuer_hold_ratio=item.issuer_hold_ratio,
            issuer_concentration_risk=features.issuer_concentration_risk,
        ),
        holder_risk=HolderRiskSummary(
            holder_count=item.holder_count,
            top_holder_ratio=item.top_holder_ratio,
            holder_concentration_risk=features.holder_concentration_risk,
            holder_evidence_missing=features.missing_holder_evidence,
        ),
        liquidity_evidence=LiquidityEvidenceSummary(
            liquidity_usd=item.liquidity_usd,
            thin_liquidity=features.thin_liquidity,
            liquidity_evidence_missing=features.missing_liquidity_evidence,
        ),
        token_control_risk=TokenControlRiskSummary(
            freeze_enabled=item.freeze_enabled,
            clawback_enabled=item.clawback_enabled,
            trustline_risk=features.freeze_clawback_risk,
        ),
        metadata_quality=MetadataQualitySummary(
            metadata_status=item.metadata_status,
            metadata_mismatch=item.metadata_mismatch,
        ),
        risk_features=features,
        reasons=tuple(reasons),
        limitations=tuple(dict.fromkeys(item.limitations)),
        missing_evidence=missing,
        fail_closed_reasons=tuple(fail_closed),
        paper_only=True,
        review_only=True,
        live_execution_allowed=False,
    )


def build_intelligence_results(items: list[IntelligenceInput]) -> list[FirstLedgerIntelligenceResult]:
    return [build_intelligence_result(item) for item in sorted(items, key=lambda row: row.candidate_id)]
