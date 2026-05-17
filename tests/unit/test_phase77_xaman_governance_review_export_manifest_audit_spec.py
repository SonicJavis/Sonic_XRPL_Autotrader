from sonic_xrpl.xaman_governance_review_export_manifest_audit_spec import (
    build_xaman_governance_review_export_manifest_audit_spec,
    load_xaman_governance_review_export_manifest_audit_fixture,
)
from sonic_xrpl.xaman_governance_review_export_manifest_audit_spec.models import (
    AUDIT_BLOCKED,
    AUDIT_INCOMPLETE,
    AUDIT_NOT_READY,
    AUDIT_REVIEW_REQUIRED,
    AUDIT_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_review_export_manifest_audit_spec.report_writer import (
    render_xaman_governance_review_export_manifest_audit_json,
    render_xaman_governance_review_export_manifest_audit_markdown,
)

BASE = "tests/fixtures/xaman_governance_review_export_manifest_audit_spec"


def _run(name):
    return build_xaman_governance_review_export_manifest_audit_spec(
        load_xaman_governance_review_export_manifest_audit_fixture(f"{BASE}/{name}")
    )


def test_phase77_complete_manifest_audit_is_spec_review_ready_and_deterministic():
    first = _run("complete_spec_review_ready_manifest_audit.json")
    second = _run("complete_spec_review_ready_manifest_audit.json")
    assert first == second
    assert first.final_audit_classification == AUDIT_SPEC_REVIEW_READY
    f = first.spec.safety_flags
    assert f.spec_only is True and f.manifest_audit_spec_only is True
    assert f.runtime_manifest_audit_service_allowed is False
    assert f.download_service_allowed is False and f.api_route_allowed is False and f.dashboard_ui_allowed is False


def test_phase77_missing_manifest_or_required_artifact_is_incomplete():
    for name in ["missing_export_manifest.json", "missing_required_artifact.json", "missing_dependency_audit_reference.json", "missing_safety_scan_reference.json"]:
        assert _run(name).final_audit_classification == AUDIT_INCOMPLETE


def test_phase77_review_findings_fail_closed_without_blocking():
    for name in [
        "hash_mismatch.json",
        "undeclared_artifact.json",
        "duplicate_artifact_id.json",
        "redaction_label_missing.json",
        "redaction_label_inconsistent.json",
        "reference_only_artifact_lacks_limitation.json",
        "reviewer_summary_missing_required_domain.json",
        "limitation_register_omits_unresolved_blocker.json",
        "cross_phase_traceability_missing.json",
    ]:
        report = _run(name)
        assert report.final_audit_classification in {AUDIT_REVIEW_REQUIRED, AUDIT_NOT_READY}
        assert report.spec.audit_findings
        assert report.spec.audit_limitation_register


def test_phase77_hidden_or_unsafe_markers_block():
    for name in [
        "hidden_expired_waiver.json",
        "hidden_revoked_waiver.json",
        "hidden_overdue_critical_sla.json",
        "hidden_unsafe_waiver_attempt.json",
        "blocked_due_xaman_payload_approval_wording.json",
        "blocked_due_wallet_material_approval_wording.json",
        "blocked_due_signing_submission_autofill_approval_wording.json",
        "blocked_due_testnet_live_execution_approval_wording.json",
        "blocked_due_runtime_manifest_audit_service_marker.json",
        "blocked_due_download_service_marker.json",
        "blocked_due_api_ui_audit_route_marker.json",
        "blocked_due_safety_bypass_marker.json",
    ]:
        report = _run(name)
        assert report.final_audit_classification == AUDIT_BLOCKED
        assert report.blockers


def test_phase77_traceability_and_reports_are_stable():
    report = _run("complete_spec_review_ready_manifest_audit.json")
    j = render_xaman_governance_review_export_manifest_audit_json(report)
    m = render_xaman_governance_review_export_manifest_audit_markdown(report)
    assert '"source_manifest_id": "manifest-76-complete"' in j
    assert '"manifest_audit_spec_only": true' in j
    assert '"audit_record_id": "rec-art-75"' in j
    assert "Still no runtime manifest audit service." in m
    assert "Still no API/UI audit route." in m
