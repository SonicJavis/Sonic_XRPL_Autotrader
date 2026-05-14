from __future__ import annotations

from sonic_xrpl.firstledger_intelligence.models import IntelligenceVerdict
from sonic_xrpl.paper_sniper_simulation.models import (
    FillAssumption,
    FillAssumptionLabel,
    PaperSniperScenario,
)


_CRITICAL_MISSING_FIELDS = {"observed_at", "ledger_index", "issuer", "currency", "tx_hash", "source_url"}


def rejection_reasons(result, scenario: PaperSniperScenario) -> tuple[str, ...]:
    reasons: list[str] = []

    verdict = result.verdict
    if verdict in {IntelligenceVerdict.AVOID, IntelligenceVerdict.INSUFFICIENT_EVIDENCE, IntelligenceVerdict.REVIEW_REQUIRED}:
        reasons.append(f"verdict_{verdict.value.lower()}")
    if verdict == IntelligenceVerdict.WATCH and not scenario.allow_watch_entry:
        reasons.append("watch_not_enabled_for_entry")
    if result.fail_closed_reasons:
        reasons.append("intelligence_fail_closed")
    if result.source_provenance.synthetic or not result.source_provenance.source_backed:
        reasons.append("synthetic_or_unbacked_evidence")
    if result.risk_features.freeze_clawback_risk:
        reasons.append("freeze_clawback_risk")
    if result.risk_features.source_conflict:
        reasons.append("source_conflict")
    if any(field in _CRITICAL_MISSING_FIELDS for field in result.missing_evidence):
        reasons.append("missing_critical_evidence")
    if result.risk_features.missing_liquidity_evidence:
        reasons.append("missing_liquidity_evidence")
    if result.risk_features.missing_holder_evidence and not scenario.allow_missing_holder_simulation:
        reasons.append("missing_holder_evidence")
    if result.launch_evidence.stale and scenario.stale_policy == "reject":
        reasons.append("stale_evidence_rejected")
    return tuple(dict.fromkeys(reasons))


def build_fill_assumption(result, scenario: PaperSniperScenario, rejected: bool) -> FillAssumption:
    if rejected:
        return FillAssumption(
            label=FillAssumptionLabel.REJECTED,
            fill_ratio=0.0,
            no_fill_reason="simulation_rejected",
            partial_fill_reason="",
            slippage_bps_assumption=max(0, scenario.slippage_bps_assumption),
            latency_seconds_assumption=max(0, scenario.latency_seconds_assumption),
            ledger_window_seconds_assumption=max(1, scenario.ledger_window_seconds_assumption),
            liquidity_available_pct_assumption=scenario.liquidity_available_pct_assumption,
        )

    liquidity = scenario.liquidity_available_pct_assumption
    slippage = max(0, scenario.slippage_bps_assumption)
    latency = max(0, scenario.latency_seconds_assumption)
    window = max(1, scenario.ledger_window_seconds_assumption)

    if liquidity is None:
        return FillAssumption(
            label=FillAssumptionLabel.NO_FILL,
            fill_ratio=0.0,
            no_fill_reason="missing_liquidity_assumption",
            partial_fill_reason="",
            slippage_bps_assumption=slippage,
            latency_seconds_assumption=latency,
            ledger_window_seconds_assumption=window,
            liquidity_available_pct_assumption=liquidity,
        )
    if liquidity <= 0:
        return FillAssumption(
            label=FillAssumptionLabel.NO_FILL,
            fill_ratio=0.0,
            no_fill_reason="thin_liquidity_no_fill",
            partial_fill_reason="",
            slippage_bps_assumption=slippage,
            latency_seconds_assumption=latency,
            ledger_window_seconds_assumption=window,
            liquidity_available_pct_assumption=liquidity,
        )
    if liquidity < 1.0:
        return FillAssumption(
            label=FillAssumptionLabel.PARTIAL_FILL,
            fill_ratio=max(0.0, min(1.0, liquidity)),
            no_fill_reason="",
            partial_fill_reason="thin_liquidity_partial_fill",
            slippage_bps_assumption=slippage,
            latency_seconds_assumption=latency,
            ledger_window_seconds_assumption=window,
            liquidity_available_pct_assumption=liquidity,
        )
    return FillAssumption(
        label=FillAssumptionLabel.FILLED,
        fill_ratio=1.0,
        no_fill_reason="",
        partial_fill_reason="",
        slippage_bps_assumption=slippage,
        latency_seconds_assumption=latency,
        ledger_window_seconds_assumption=window,
        liquidity_available_pct_assumption=liquidity,
    )
