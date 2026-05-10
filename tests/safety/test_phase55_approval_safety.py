from pathlib import Path

from sonic_xrpl.calibration_approval import build_approval_ledger


def test_phase55_all_records_keep_safe_flags():
    ledger = build_approval_ledger(
        "tests/fixtures/calibration_proposal/ready_for_review_recommendations.json",
        "tests/fixtures/calibration_approval/approved_change_request.json",
    )

    for record in ledger.records:
        assert record.paper_only is True
        assert record.offline_only is True
        assert record.live_execution_allowed is False
        assert record.auto_apply_allowed is False
        assert record.runtime_mutation_allowed is False
        assert record.requires_human_review is True
    for request in ledger.change_requests:
        assert request.apply_allowed is False
        assert request.live_execution_allowed is False
        assert request.runtime_mutation_allowed is False


def test_phase55_package_has_no_forbidden_execution_terms():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/calibration_approval").glob("*.py"))
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
        "requests.get(",
        "requests.post(",
    ]
    for term in forbidden:
        assert term not in combined
