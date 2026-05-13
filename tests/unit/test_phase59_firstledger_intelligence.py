from pathlib import Path

from sonic_xrpl.firstledger_intelligence import build_intelligence_results
from sonic_xrpl.firstledger_intelligence.loader import load_firstledger_intelligence_inputs
from sonic_xrpl.firstledger_intelligence.models import IntelligenceVerdict
from sonic_xrpl.firstledger_intelligence.reporting import render_intelligence_markdown, render_intelligence_report


def _results(name: str):
    fixture = Path("tests/fixtures/firstledger_intelligence") / name
    return build_intelligence_results(load_firstledger_intelligence_inputs(fixture))


def test_source_backed_healthy_can_be_paper_only_candidate():
    item = _results("source_backed_healthy.json")[0]
    assert item.verdict == IntelligenceVerdict.PAPER_ONLY_CANDIDATE
    assert item.paper_only is True
    assert item.review_only is True
    assert item.live_execution_allowed is False


def test_synthetic_only_is_insufficient_evidence():
    item = _results("synthetic_only.json")[0]
    assert item.verdict == IntelligenceVerdict.INSUFFICIENT_EVIDENCE
    assert "Synthetic evidence cannot qualify as paper-only candidate." in item.reasons


def test_missing_launch_timestamp_is_missing_evidence():
    item = _results("missing_launch_timestamp.json")[0]
    assert item.verdict == IntelligenceVerdict.INSUFFICIENT_EVIDENCE
    assert "observed_at" in item.missing_evidence


def test_stale_evidence_sets_stale_marker():
    item = _results("stale_evidence.json")[0]
    assert item.launch_evidence.stale is True
    assert item.launch_evidence.stale_reason == "stale_over_48h"


def test_concentration_and_token_controls_risk_labels():
    issuer = _results("issuer_concentration_risk.json")[0]
    holder = _results("holder_concentration_risk.json")[0]
    freeze = _results("freeze_clawback_risk.json")[0]
    assert issuer.risk_features.issuer_concentration_risk is True
    assert holder.risk_features.holder_concentration_risk is True
    assert freeze.risk_features.freeze_clawback_risk is True
    assert freeze.verdict == IntelligenceVerdict.AVOID


def test_conflicting_source_evidence_requires_review():
    item = _results("conflicting_source_evidence.json")[0]
    assert item.risk_features.source_conflict is True
    assert item.verdict == IntelligenceVerdict.REVIEW_REQUIRED


def test_missing_liquidity_evidence_flagged():
    item = _results("missing_liquidity_evidence.json")[0]
    assert item.risk_features.missing_liquidity_evidence is True
    assert item.liquidity_evidence.liquidity_evidence_missing is True


def test_same_symbol_different_issuer_not_collapsed():
    items = _results("same_symbol_different_issuer.json")
    assert len(items) == 2
    assert {item.issuer for item in items} == {
        "rSymbolIssuerA111111111111111111111",
        "rSymbolIssuerB111111111111111111111",
    }
    assert all(item.risk_features.same_symbol_different_issuer for item in items)


def test_malformed_source_record_fails_closed():
    item = _results("malformed_source_record.json")[0]
    assert item.verdict == IntelligenceVerdict.INSUFFICIENT_EVIDENCE
    assert "malformed_source_record" in item.fail_closed_reasons


def test_reporting_outputs_are_deterministic_and_non_executing():
    results = _results("source_backed_healthy.json")
    payload = render_intelligence_report(results)
    markdown = render_intelligence_markdown(results)
    assert payload[0]["live_execution_allowed"] is False
    assert payload[0]["paper_only"] is True
    assert "non-executing intelligence output" in markdown
