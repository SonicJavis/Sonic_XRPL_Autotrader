from sonic_xrpl.calibration_approval.models import (
    ApprovalLedger,
    CalibrationApprovalRecord,
    CalibrationChangeRequest,
    HumanReviewer,
)


def test_phase55_model_defaults_are_safe():
    reviewer = HumanReviewer(reviewer_id="reviewer")
    record = CalibrationApprovalRecord(
        approval_record_id="car_test",
        proposal_pack_id="pack",
        proposal_id="proposal",
        proposal_signal_class="watch_threshold",
        proposal_direction="REVIEW_DECREASE",
        proposal_before_value=0.5,
        proposal_after_value=0.48,
        proposal_delta=-0.02,
        reviewer=reviewer,
        decision="APPROVED_FOR_CHANGE_REQUEST",
        decision_reason="reviewed",
        reviewer_notes="notes",
        evidence_summary="evidence",
        limitation_summary=(),
        safety_flags={},
        deterministic_hash="hash",
        content_hash="hash",
    )
    request = CalibrationChangeRequest(
        change_request_id="ccr_test",
        approval_record_id=record.approval_record_id,
        proposal_pack_id=record.proposal_pack_id,
        proposal_id=record.proposal_id,
        requested_change="watch_threshold",
        before_value=0.5,
        after_value=0.48,
        delta=-0.02,
        rationale="reviewed",
        required_follow_up=(),
    )

    assert record.paper_only is True
    assert record.offline_only is True
    assert record.live_execution_allowed is False
    assert record.auto_apply_allowed is False
    assert record.runtime_mutation_allowed is False
    assert record.requires_human_review is True
    assert request.change_request_only is True
    assert request.apply_allowed is False
    assert request.runtime_mutation_allowed is False
    assert request.live_execution_allowed is False


def test_ledger_counts_are_explicit():
    ledger = ApprovalLedger(
        ledger_id="ledger",
        records=(),
        change_requests=(),
        counts_by_decision={},
        counts_by_change_request_status={},
        blocked_count=0,
        approved_count=0,
        invalid_count=0,
        generated_at="1970-01-01T00:00:00+00:00",
        safety_summary="safe",
        limitation_summary=(),
    )

    assert ledger.generated_at == "1970-01-01T00:00:00+00:00"
    assert ledger.change_requests == ()
