from pathlib import Path

from sonic_xrpl.firstledger_intelligence import build_intelligence_results
from sonic_xrpl.firstledger_intelligence.loader import load_firstledger_intelligence_inputs
from sonic_xrpl.firstledger_intelligence.models import IntelligenceVerdict


def _results(path: str):
    return build_intelligence_results(load_firstledger_intelligence_inputs(path))


def test_firstledger_intelligence_layer_forbidden_runtime_terms_absent():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/firstledger_intelligence").glob("*.py"))
    forbidden = [
        "submitAndWait",
        "autofill",
        "fromSeed",
        "familySeed",
        "Wallet(",
        "Xaman",
        "Xumm",
        "OfferCreate",
        "Payment",
        "TrustSet",
    ]
    for term in forbidden:
        assert term not in combined


def test_synthetic_only_cannot_produce_positive_candidate():
    item = _results("tests/fixtures/firstledger_intelligence/synthetic_only.json")[0]
    assert item.verdict in {IntelligenceVerdict.INSUFFICIENT_EVIDENCE, IntelligenceVerdict.REVIEW_REQUIRED}
    assert item.verdict != IntelligenceVerdict.PAPER_ONLY_CANDIDATE


def test_positive_labels_are_explicitly_paper_only_and_non_executing():
    for name in (
        "source_backed_healthy.json",
        "issuer_concentration_risk.json",
        "holder_concentration_risk.json",
    ):
        for item in _results(f"tests/fixtures/firstledger_intelligence/{name}"):
            assert item.paper_only is True
            assert item.review_only is True
            assert item.live_execution_allowed is False


def test_missing_critical_evidence_fails_closed():
    item = _results("tests/fixtures/firstledger_intelligence/missing_launch_timestamp.json")[0]
    assert item.verdict == IntelligenceVerdict.INSUFFICIENT_EVIDENCE
    assert "observed_at" in item.missing_evidence
