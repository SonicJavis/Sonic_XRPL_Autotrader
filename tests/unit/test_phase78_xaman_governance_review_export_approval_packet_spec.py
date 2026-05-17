from sonic_xrpl.xaman_governance_review_export_approval_packet_spec import (
    build_xaman_governance_review_export_approval_packet_spec,
    load_xaman_governance_review_export_approval_packet_fixture,
)
from sonic_xrpl.xaman_governance_review_export_approval_packet_spec.models import (
    APPROVAL_PACKET_BLOCKED,
    APPROVAL_PACKET_INCOMPLETE,
    APPROVAL_PACKET_NOT_READY,
    APPROVAL_PACKET_REVIEW_REQUIRED,
    APPROVAL_PACKET_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_review_export_approval_packet_spec.report_writer import (
    render_xaman_governance_review_export_approval_packet_json,
    render_xaman_governance_review_export_approval_packet_markdown,
)

BASE = "tests/fixtures/xaman_governance_review_export_approval_packet_spec"


def _run(name):
    return build_xaman_governance_review_export_approval_packet_spec(
        load_xaman_governance_review_export_approval_packet_fixture(f"{BASE}/{name}")
    )


def test_phase78_complete_packet_is_spec_review_ready_and_deterministic():
    first = _run("complete_spec_review_ready_approval_packet.json")
    second = _run("complete_spec_review_ready_approval_packet.json")
    assert first == second
    assert first.final_packet_classification == APPROVAL_PACKET_SPEC_REVIEW_READY
    f = first.spec.safety_flags
    assert f.spec_only is True and f.approval_packet_spec_only is True
    assert f.runtime_approval_service_allowed is False


def test_phase78_missing_inputs_are_incomplete_or_review_required():
    assert _run("missing_export_package.json").final_packet_classification == APPROVAL_PACKET_INCOMPLETE
    assert _run("missing_manifest_audit.json").final_packet_classification == APPROVAL_PACKET_INCOMPLETE
    for name in ["incomplete_manifest_audit.json", "manifest_audit_review_required.json", "missing_security_acknowledgement.json", "unresolved_acknowledgement_limitation.json", "unresolved_blocker_hidden.json", "unresolved_limitation_hidden.json", "expired_waiver_unresolved.json", "revoked_waiver_unresolved.json", "dependency_audit_unresolved.json", "safety_review_unresolved.json"]:
        assert _run(name).final_packet_classification in {APPROVAL_PACKET_REVIEW_REQUIRED, APPROVAL_PACKET_NOT_READY}


def test_phase78_blocked_paths_fail_closed():
    for name in [
        "blocked_manifest_audit.json",
        "rejected_reviewer_acknowledgement.json",
        "overdue_sla_unresolved.json",
        "unsafe_waiver_attempt_unresolved.json",
        "blocked_due_xaman_payload_approval_wording.json",
        "blocked_due_wallet_material_approval_wording.json",
        "blocked_due_signing_submission_autofill_approval_wording.json",
        "blocked_due_testnet_live_execution_approval_wording.json",
        "blocked_due_runtime_approval_service_marker.json",
        "blocked_due_download_service_marker.json",
        "blocked_due_api_ui_approval_route_marker.json",
        "blocked_due_safety_bypass_marker.json",
    ]:
        report = _run(name)
        assert report.final_packet_classification == APPROVAL_PACKET_BLOCKED
        assert report.blockers


def test_phase78_notices_traceability_and_reports_are_stable():
    report = _run("complete_spec_review_ready_approval_packet.json")
    j = render_xaman_governance_review_export_approval_packet_json(report)
    m = render_xaman_governance_review_export_approval_packet_markdown(report)
    assert '"source_manifest_audit_id": "audit-77-complete"' in j
    assert '"approval_packet_spec_only": true' in j
    assert "no payload creation authorized" in m
    assert "Still no runtime approval service." in m
    assert "Still no API/UI approval route." in m
