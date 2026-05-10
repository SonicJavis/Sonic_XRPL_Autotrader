from sonic_xrpl.calibration_approval import build_approval_ledger


def test_change_request_is_artifact_only():
    ledger = build_approval_ledger(
        "tests/fixtures/calibration_proposal/ready_for_review_recommendations.json",
        "tests/fixtures/calibration_approval/approved_change_request.json",
    )
    request = ledger.change_requests[0]

    assert request.status == "REQUESTED"
    assert request.change_request_only is True
    assert request.apply_allowed is False
    assert request.live_execution_allowed is False
    assert request.runtime_mutation_allowed is False
    assert request.before_value == 0.5
    assert request.after_value == 0.48
    assert request.delta == -0.02
