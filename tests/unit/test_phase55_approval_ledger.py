from sonic_xrpl.calibration_approval import build_approval_ledger


READY_PROPOSAL = "tests/fixtures/calibration_proposal/ready_for_review_recommendations.json"
PHASE54_PROPOSAL_PACK = "reports/phase54/calibration_proposal_pack.json"


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


def test_phase54_proposal_pack_loads_existing_proposals_for_approval():
    ledger = build_approval_ledger(
        PHASE54_PROPOSAL_PACK,
        "tests/fixtures/calibration_approval/approved_change_request.json",
    )

    assert len(ledger.records) == 1
    assert len(ledger.change_requests) == 1
    assert ledger.records[0].decision == "APPROVED_FOR_CHANGE_REQUEST"
    assert ledger.records[0].proposal_id == "cp_5bc3f4608f9e68e55d14d5ac"
    assert ledger.change_requests[0].proposal_id == "cp_5bc3f4608f9e68e55d14d5ac"
    assert ledger.records[0].live_execution_allowed is False
    assert ledger.records[0].auto_apply_allowed is False
    assert ledger.records[0].runtime_mutation_allowed is False


def test_empty_reviews_create_empty_ledger():
    ledger = build_approval_ledger(READY_PROPOSAL, "tests/fixtures/calibration_approval/empty_reviews.json")

    assert ledger.records == ()
    assert ledger.change_requests == ()
