from sonic_xrpl.xaman_governance_final_readiness_bundle_spec import (
    build_xaman_governance_final_readiness_bundle_spec,
    load_xaman_governance_final_readiness_bundle_fixture,
)
from sonic_xrpl.xaman_governance_final_readiness_bundle_spec.models import (
    FINAL_BLOCKED,
    FINAL_INCOMPLETE,
    FINAL_NOT_READY,
    FINAL_REVIEW_REQUIRED,
    FINAL_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_final_readiness_bundle_spec.report_writer import (
    render_xaman_governance_final_readiness_bundle_json,
    render_xaman_governance_final_readiness_bundle_markdown,
)
BASE="tests/fixtures/xaman_governance_final_readiness_bundle_spec"
def _run(name): return build_xaman_governance_final_readiness_bundle_spec(load_xaman_governance_final_readiness_bundle_fixture(f"{BASE}/{name}"))

def test_phase75_complete_bundle_is_spec_review_ready_and_deterministic():
    first=_run("complete_spec_review_ready_final_bundle.json"); second=_run("complete_spec_review_ready_final_bundle.json")
    assert first==second
    assert first.final_readiness_classification==FINAL_SPEC_REVIEW_READY
    f=first.spec.safety_flags
    assert f.spec_only is True and f.final_readiness_bundle_spec_only is True
    assert f.runtime_readiness_service_allowed is False and f.safety_bypass_allowed is False
    assert f.testnet_execution_allowed is False and f.live_execution_allowed is False

def test_phase75_missing_mandatory_phase_artifacts_are_incomplete():
    for name in ["missing_phase70_report.json","missing_phase71_attestation_report.json","missing_phase72_workflow_report.json","missing_phase73_sla_report.json","missing_phase74_waiver_report.json"]:
        assert _run(name).final_readiness_classification==FINAL_INCOMPLETE

def test_phase75_review_states_preserve_unresolved_limitations():
    for name in ["unresolved_safety_review.json","unresolved_dependency_risk.json","expired_waiver.json","revoked_waiver.json","ambiguous_signoff_linkage.json","missing_rollback_evidence.json","missing_incident_response_evidence.json"]:
        report=_run(name)
        assert report.final_readiness_classification in {FINAL_REVIEW_REQUIRED, FINAL_NOT_READY}
        assert report.spec.limitation_register

def test_phase75_blockers_fail_closed():
    for name in ["overdue_critical_sla.json","unsafe_waiver_attempt.json","blocked_due_xaman_payload_approval_wording.json","blocked_due_wallet_material_approval_wording.json","blocked_due_signing_submission_autofill_approval_wording.json","blocked_due_testnet_live_execution_approval_wording.json","blocked_due_runtime_readiness_service_marker.json","blocked_due_safety_bypass_marker.json"]:
        report=_run(name)
        assert report.final_readiness_classification==FINAL_BLOCKED
        assert report.blockers

def test_phase75_traceability_and_reports_are_stable():
    report=_run("complete_spec_review_ready_final_bundle.json")
    j=render_xaman_governance_final_readiness_bundle_json(report); m=render_xaman_governance_final_readiness_bundle_markdown(report)
    assert '"artifact_type": "PHASE70_SIGNOFF_MATRIX_REPORT"' in j
    assert '"runtime_readiness_service_allowed": false' in j
    assert '"final_readiness_bundle_spec_only": true' in j
    assert "Still no runtime readiness service." in m
    assert "Still no safety bypass." in m
