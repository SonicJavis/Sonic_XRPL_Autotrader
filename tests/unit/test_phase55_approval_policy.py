from sonic_xrpl.calibration_approval import build_approval_ledger


PROPOSAL_FIXTURE = "tests/fixtures/calibration_proposal/ready_for_review_recommendations.json"


def test_approved_valid_review_creates_change_request():
    ledger = build_approval_ledger(PROPOSAL_FIXTURE, "tests/fixtures/calibration_approval/approved_change_request.json")

    assert ledger.approved_count == 1
    assert len(ledger.change_requests) == 1
    assert ledger.change_requests[0].apply_allowed is False
    assert ledger.change_requests[0].runtime_mutation_allowed is False


def test_rejected_deferred_and_revision_create_no_change_request():
    for fixture in (
        "tests/fixtures/calibration_approval/rejected_review.json",
        "tests/fixtures/calibration_approval/deferred_review.json",
        "tests/fixtures/calibration_approval/needs_revision_review.json",
    ):
        ledger = build_approval_ledger(PROPOSAL_FIXTURE, fixture)
        assert ledger.change_requests == ()
        assert ledger.records[0].decision in {"REJECTED", "DEFERRED", "NEEDS_REVISION"}


def test_missing_reviewer_blocks_approval():
    ledger = build_approval_ledger(PROPOSAL_FIXTURE, "tests/fixtures/calibration_approval/missing_reviewer.json")

    assert ledger.change_requests == ()
    assert ledger.records[0].decision == "BLOCKED"
    assert "reviewer_id_missing" in ledger.records[0].limitation_summary


def test_missing_decision_reason_blocks_approval():
    ledger = build_approval_ledger(PROPOSAL_FIXTURE, "tests/fixtures/calibration_approval/missing_decision_reason.json")

    assert ledger.change_requests == ()
    assert ledger.records[0].decision == "BLOCKED"
    assert "decision_reason_missing" in ledger.records[0].limitation_summary
