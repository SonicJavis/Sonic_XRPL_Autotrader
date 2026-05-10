from sonic_xrpl.calibration_approval import build_approval_ledger


READY_PROPOSAL = "tests/fixtures/calibration_proposal/ready_for_review_recommendations.json"


def test_blocked_phase54_proposal_remains_blocked():
    ledger = build_approval_ledger(
        "tests/fixtures/calibration_proposal/insufficient_evidence_recommendations.json",
        "tests/fixtures/calibration_approval/blocked_phase54_proposal.json",
    )

    assert ledger.change_requests == ()
    assert ledger.records[0].decision == "BLOCKED"
    assert "proposal_not_found_or_blocked" in ledger.records[0].limitation_summary


def test_synthetic_and_invalid_inputs_remain_blocked():
    cases = (
        (
            "tests/fixtures/calibration_proposal/synthetic_heavy_recommendations.json",
            "tests/fixtures/calibration_approval/synthetic_heavy_proposal_review.json",
        ),
        (
            "tests/fixtures/calibration_proposal/invalid_observation_recommendations.json",
            "tests/fixtures/calibration_approval/invalid_numeric_proposal_review.json",
        ),
    )
    for proposal_fixture, review_fixture in cases:
        ledger = build_approval_ledger(proposal_fixture, review_fixture)
        assert ledger.change_requests == ()
        assert ledger.records[0].decision == "BLOCKED"


def test_mixed_ledger_counts_and_deterministic_ids():
    first = build_approval_ledger(READY_PROPOSAL, "tests/fixtures/calibration_approval/mixed_approval_ledger.json")
    second = build_approval_ledger(READY_PROPOSAL, "tests/fixtures/calibration_approval/mixed_approval_ledger.json")

    assert first.ledger_id == second.ledger_id
    assert [record.approval_record_id for record in first.records] == [record.approval_record_id for record in second.records]
    assert len(first.records) == 2
    assert len(first.change_requests) == 1
    assert first.counts_by_decision["APPROVED_FOR_CHANGE_REQUEST"] == 1
    assert first.counts_by_decision["REJECTED"] == 1


def test_empty_reviews_create_empty_ledger():
    ledger = build_approval_ledger(READY_PROPOSAL, "tests/fixtures/calibration_approval/empty_reviews.json")

    assert ledger.records == ()
    assert ledger.change_requests == ()
