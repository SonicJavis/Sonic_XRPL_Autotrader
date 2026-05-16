from sonic_xrpl.xaman_governance_evidence_review_workflow_spec import (
    build_xaman_governance_evidence_review_workflow_spec,
    load_xaman_governance_evidence_review_workflow_fixture,
)
from sonic_xrpl.xaman_governance_evidence_review_workflow_spec.models import (
    WORKFLOW_BLOCKED,
    WORKFLOW_NOT_READY,
    WORKFLOW_REVIEW_REQUIRED,
    WORKFLOW_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_evidence_review_workflow_spec.report_writer import (
    render_xaman_governance_evidence_review_workflow_json,
    render_xaman_governance_evidence_review_workflow_markdown,
)


def _run(path: str):
    return build_xaman_governance_evidence_review_workflow_spec(
        load_xaman_governance_evidence_review_workflow_fixture(path)
    )


def test_phase72_complete_workflow_is_spec_review_ready():
    report = _run(
        "tests/fixtures/xaman_governance_evidence_review_workflow_spec/complete_spec_review_ready_workflow.json"
    )
    assert report.readiness_classification == WORKFLOW_SPEC_REVIEW_READY
    f = report.spec.safety_flags
    assert f.spec_only is True
    assert f.workflow_spec_only is True
    assert f.runtime_workflow_allowed is False
    assert f.testnet_execution_allowed is False
    assert f.live_execution_allowed is False


def test_phase72_missing_or_review_conditions_are_conservative():
    for name in [
        "missing_evidence_intake.json",
        "stale_evidence_escalation.json",
        "hash_mismatch_escalation.json",
        "synthetic_only_review_required.json",
        "missing_reviewer_escalation.json",
        "ambiguous_signoff_linkage.json",
        "dependency_report_missing.json",
        "safety_scan_untriaged.json",
        "rollback_evidence_missing.json",
        "incident_response_evidence_missing.json",
        "rejected_workflow.json",
        "deferred_workflow.json",
    ]:
        report = _run(f"tests/fixtures/xaman_governance_evidence_review_workflow_spec/{name}")
        assert report.readiness_classification in {WORKFLOW_REVIEW_REQUIRED, WORKFLOW_NOT_READY, WORKFLOW_SPEC_REVIEW_READY}


def test_phase72_unsafe_markers_block():
    for name in [
        "blocked_payload_testnet_live_wording.json",
        "blocked_wallet_material_ambiguity.json",
        "blocked_runtime_workflow_marker.json",
    ]:
        report = _run(f"tests/fixtures/xaman_governance_evidence_review_workflow_spec/{name}")
        assert report.readiness_classification == WORKFLOW_BLOCKED
        assert report.blockers


def test_phase72_reporting_includes_runtime_workflow_statement():
    report = _run(
        "tests/fixtures/xaman_governance_evidence_review_workflow_spec/complete_spec_review_ready_workflow.json"
    )
    as_json = render_xaman_governance_evidence_review_workflow_json(report)
    as_md = render_xaman_governance_evidence_review_workflow_markdown(report)
    assert '"runtime_workflow_allowed": false' in as_json
    assert "Still no runtime workflow engine." in as_md
