from pathlib import Path

from sonic_xrpl.calibration_review import (
    build_threshold_recommendations,
    evaluate_readiness,
    load_evidence_snapshot,
)


def test_phase53_runtime_has_no_forbidden_execution_terms():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/calibration_review").glob("*.py"))
    forbidden = [
        "submitAndWait",
        "autofill",
        "Xaman",
        "fromSeed",
        "familySeed",
        "auto-buy",
        "place_order",
        "while True",
        "websocket",
        "requests.",
    ]
    for term in forbidden:
        assert term not in combined


def test_phase53_live_execution_remains_false():
    snapshot = load_evidence_snapshot("tests/fixtures/calibration_review/sufficient_source_backed_evidence.json")
    result = evaluate_readiness(snapshot)
    recs = build_threshold_recommendations(result)

    assert snapshot.live_execution_allowed is False
    assert result.live_execution_allowed is False
    assert all(item.live_execution_allowed is False for item in recs)


def test_phase53_live_enabled_fixture_is_blocked():
    snapshot = load_evidence_snapshot("tests/fixtures/calibration_review/live_enabled_blocker.json")
    result = evaluate_readiness(snapshot)

    assert snapshot.live_enabled_records
    assert result.status != "READY_FOR_HUMAN_REVIEW"
    assert result.blockers
