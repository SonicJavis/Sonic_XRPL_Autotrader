"""Quality scoring for market snapshots — Phase 47.

Score starts at 100 and is reduced by missing/stale/invalid data.
Rules are documented in docs/research/PHASE47_MARKET_SNAPSHOT_RESEARCH.md.
"""

from __future__ import annotations

from typing import Any

from sonic_xrpl.market.models import SnapshotQuality, SnapshotRecommendation


_SCORE_DEDUCTIONS = {
    "missing_metadata": 20,
    "tes_success_no_nodes": 15,
    "missing_amm": 10,
    "missing_orderbook": 10,
    "mpt_unavailable": 5,
    "capability_mismatch": 5,
    "missing_account": 5,
    "fixture_health_warning": 5,
}

_THRESHOLD_SIMULATION = 80
_THRESHOLD_RESEARCH = 50
_THRESHOLD_INSUFFICIENT = 20


def _recommendation(score: int) -> SnapshotRecommendation:
    if score >= _THRESHOLD_SIMULATION:
        return SnapshotRecommendation.USABLE_FOR_SIMULATION
    if score >= _THRESHOLD_RESEARCH:
        return SnapshotRecommendation.USABLE_FOR_RESEARCH
    if score >= _THRESHOLD_INSUFFICIENT:
        return SnapshotRecommendation.INSUFFICIENT_DATA
    return SnapshotRecommendation.REJECTED


def score_snapshot(
    *,
    manifest_valid: bool,
    has_amm_data: bool,
    amm_requested: bool,
    has_orderbook_data: bool,
    has_metadata: bool,
    metadata_sufficient_truth: bool,
    has_mpt_data: bool,
    mpt_requested: bool,
    has_account_data: bool,
    account_requested: bool,
    capability_warnings: list[str],
    fixture_warnings: list[str],
    xahau_hooks_context: bool = False,
) -> SnapshotQuality:
    """Compute snapshot quality score and recommendation.

    Rules:
    - Score starts at 100.
    - Invalid manifest → rejected immediately.
    - Missing metadata caps score (deduct 20).
    - tesSUCCESS without AffectedNodes caps score (deduct 15).
    - Missing AMM when requested (deduct 10).
    - Missing orderbook data (deduct 10).
    - MPT requested but unavailable (deduct 5).
    - Missing account when requested (deduct 5).
    - Each capability mismatch warning (deduct 5 each, max −20).
    - Fixture health warnings (deduct 5 each, max −20).
    - Xahau/Hooks context must NOT improve XRPL mainnet confidence.
    """
    if not manifest_valid:
        return SnapshotQuality(
            score=0,
            coverage={},
            missing_sections=["manifest"],
            stale_sections=[],
            protocol_warnings=["fixture manifest is invalid"],
            fixture_warnings=fixture_warnings,
            recommendation=SnapshotRecommendation.REJECTED,
        )

    score = 100
    missing_sections: list[str] = []
    stale_sections: list[str] = []
    protocol_warnings: list[str] = list(capability_warnings)

    if not has_metadata:
        score -= _SCORE_DEDUCTIONS["missing_metadata"]
        missing_sections.append("metadata")

    if has_metadata and not metadata_sufficient_truth:
        score -= _SCORE_DEDUCTIONS["tes_success_no_nodes"]
        protocol_warnings.append("tesSUCCESS metadata present but AffectedNodes missing — not sufficient truth")

    if amm_requested and not has_amm_data:
        score -= _SCORE_DEDUCTIONS["missing_amm"]
        missing_sections.append("amm")

    if not has_orderbook_data:
        score -= _SCORE_DEDUCTIONS["missing_orderbook"]
        missing_sections.append("orderbook")

    if mpt_requested and not has_mpt_data:
        score -= _SCORE_DEDUCTIONS["mpt_unavailable"]
        missing_sections.append("mpt")

    if account_requested and not has_account_data:
        score -= _SCORE_DEDUCTIONS["missing_account"]
        missing_sections.append("accounts")

    cap_deduction = min(len(capability_warnings) * _SCORE_DEDUCTIONS["capability_mismatch"], 20)
    score -= cap_deduction

    fix_deduction = min(len(fixture_warnings) * _SCORE_DEDUCTIONS["fixture_health_warning"], 20)
    score -= fix_deduction

    if xahau_hooks_context:
        protocol_warnings.append(
            "Xahau/Hooks context present — does NOT improve XRPL mainnet confidence"
        )

    score = max(0, score)

    coverage = {
        "manifest": manifest_valid,
        "amm": has_amm_data,
        "orderbook": has_orderbook_data,
        "metadata": has_metadata,
        "metadata_sufficient_truth": metadata_sufficient_truth,
        "mpt": has_mpt_data,
        "accounts": has_account_data,
    }

    return SnapshotQuality(
        score=score,
        coverage=coverage,
        missing_sections=missing_sections,
        stale_sections=stale_sections,
        protocol_warnings=protocol_warnings,
        fixture_warnings=fixture_warnings,
        recommendation=_recommendation(score),
    )
