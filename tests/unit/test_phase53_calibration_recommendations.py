from pathlib import Path

from sonic_xrpl.calibration_review import (
    build_threshold_recommendations,
    evaluate_readiness,
    load_evidence_snapshot,
)


BASE = "tests/fixtures/calibration_review"


def recommendations(name: str):
    result = evaluate_readiness(load_evidence_snapshot(f"{BASE}/{name}.json"))
    return result, build_threshold_recommendations(result)


def test_phase53_insufficient_evidence_keeps_thresholds_non_mutating():
    _, recs = recommendations("insufficient_evidence")

    assert recs
    assert all(item.non_mutating for item in recs)
    assert all(item.requires_human_review for item in recs)
    assert any(item.direction == "INSUFFICIENT_EVIDENCE" for item in recs)
    assert all("Set threshold to" not in item.rationale for item in recs)


def test_phase53_sparse_classes_do_not_produce_confident_directional_threshold_review():
    result, recs = recommendations("sparse_signal_classes")

    assert result.status == "REVIEW_WITH_CAUTION"
    assert not any(
        item.target in {"watch_threshold", "signal_score_threshold"}
        and item.direction in {"REVIEW_INCREASE", "REVIEW_DECREASE"}
        for item in recs
    )


def test_phase53_advisory_wording_has_no_forbidden_trading_claims():
    _, recs = recommendations("sufficient_source_backed_evidence")
    combined = " ".join(item.rationale.lower() for item in recs)

    assert "strong buy" not in combined
    assert "moonshot" not in combined
    assert "profitability" not in combined
    assert "enable live" not in combined
    assert "apply new threshold" not in combined


def test_phase53_review_layer_does_not_modify_scoring_modules():
    watched = [
        Path("src/sonic_xrpl/signals/scoring.py"),
        Path("src/sonic_xrpl/review/decision_policy.py"),
        Path("src/sonic_xrpl/outcomes/attribution.py"),
        Path("src/sonic_xrpl/outcome_corpus/quality.py"),
    ]
    before = {path: path.read_text(encoding="utf-8") for path in watched}
    recommendations("sufficient_source_backed_evidence")
    after = {path: path.read_text(encoding="utf-8") for path in watched}

    assert before == after
