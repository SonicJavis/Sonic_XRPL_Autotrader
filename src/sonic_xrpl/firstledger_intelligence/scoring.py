from __future__ import annotations

from sonic_xrpl.firstledger_intelligence.models import IntelligenceInput, RiskFeatureSummary


def build_risk_features(item: IntelligenceInput) -> RiskFeatureSummary:
    issuer_concentration = (item.issuer_hold_ratio or 0.0) >= 0.5
    holder_concentration = (item.top_holder_ratio or 0.0) >= 0.6
    missing_holder = item.holder_count is None or item.top_holder_ratio is None
    missing_liquidity = item.liquidity_usd is None
    thin_liquidity = (item.liquidity_usd or 0.0) < 5000 if item.liquidity_usd is not None else False
    freeze_clawback = bool(item.freeze_enabled) or bool(item.clawback_enabled)
    metadata_mismatch = bool(item.metadata_mismatch)
    same_symbol_diff_issuer = bool(item.same_symbol_different_issuer)
    source_conflict = bool(item.source_conflict)
    unsupported_capability = "unsupported_capability" in item.limitations
    return RiskFeatureSummary(
        issuer_concentration_risk=issuer_concentration,
        holder_concentration_risk=holder_concentration,
        missing_holder_evidence=missing_holder,
        missing_liquidity_evidence=missing_liquidity,
        thin_liquidity=thin_liquidity,
        freeze_clawback_risk=freeze_clawback,
        metadata_mismatch_risk=metadata_mismatch,
        same_symbol_different_issuer=same_symbol_diff_issuer,
        source_conflict=source_conflict,
        unsupported_capability_evidence=unsupported_capability,
    )


def score_confidence(item: IntelligenceInput, features: RiskFeatureSummary) -> int:
    score = 100
    if not item.source_backed:
        score -= 45
    if not item.source_trust_known:
        score -= 15
    if item.synthetic:
        score -= 35
    if not item.observed_at:
        score -= 25
    if item.stale_hours is not None and item.stale_hours > 48:
        score -= 15
    if item.metadata_status != "validated":
        score -= 12
    if features.issuer_concentration_risk:
        score -= 12
    if features.holder_concentration_risk:
        score -= 12
    if features.missing_holder_evidence:
        score -= 15
    if features.missing_liquidity_evidence:
        score -= 20
    if features.thin_liquidity:
        score -= 8
    if features.freeze_clawback_risk:
        score -= 18
    if features.metadata_mismatch_risk:
        score -= 15
    if features.same_symbol_different_issuer:
        score -= 10
    if features.source_conflict:
        score -= 20
    if item.malformed_source_record:
        score = 0
    return max(0, min(100, score))


def confidence_band(score: int) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"
