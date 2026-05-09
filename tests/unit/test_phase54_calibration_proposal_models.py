from sonic_xrpl.calibration_proposal.models import (
    DETERMINISTIC_CREATED_AT,
    CalibrationParameterRef,
    CalibrationProposal,
    CalibrationProposalPack,
    ProposalRiskSummary,
)


def test_phase54_model_defaults_are_safe():
    parameter = CalibrationParameterRef(
        namespace="paper_calibration",
        name="watch_threshold",
        description="test",
        current_value=0.5,
        proposed_value=0.48,
        value_type="ratio",
        allowed_range=(0.0, 1.0),
        unit="ratio",
        source="fixture",
    )
    proposal = CalibrationProposal(
        proposal_id="cp_test",
        created_at=DETERMINISTIC_CREATED_AT,
        phase="54",
        source_readiness_id="cr_test",
        source_recommendation_id="tr_test",
        parameter_ref=parameter,
        direction="REVIEW_DECREASE",
        exact_delta=-0.02,
        current_value=0.5,
        proposed_value=0.48,
        confidence=0.65,
        evidence_summary="test",
        supporting_evidence_ids=("evidence",),
        limitations=(),
        risk_notes=(),
        rollback_note="revert",
    )

    assert proposal.human_review_required is True
    assert proposal.auto_apply_allowed is False
    assert proposal.live_execution_allowed is False
    assert proposal.status == "PROPOSED_FOR_HUMAN_REVIEW"


def test_phase54_pack_defaults_are_safe():
    risk = ProposalRiskSummary(
        risk_level="LOW",
        reasons=("source-backed",),
        evidence_quality="A",
        synthetic_ratio=0.0,
        missing_observation_count=0,
        invalid_observation_count=0,
        sparse_class_warnings=(),
    )
    pack = CalibrationProposalPack(
        pack_id="cpp_test",
        created_at=DETERMINISTIC_CREATED_AT,
        phase="54",
        input_summary={},
        proposals=(),
        blocked_recommendations=(),
        review_checklist=(),
        approval_requirements=(),
        safety_statement="No settings were changed.",
        limitations=(),
        risk_summary=risk,
    )

    assert pack.paper_only is True
    assert pack.auto_apply_allowed is False
    assert pack.live_execution_allowed is False
