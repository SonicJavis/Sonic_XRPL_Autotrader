from sonic_xrpl.xaman_governance_final_readiness_review_export_spec import (
    build_xaman_governance_final_readiness_review_export_spec,
    load_xaman_governance_final_readiness_review_export_fixture,
)
from sonic_xrpl.xaman_governance_final_readiness_review_export_spec.models import (
    EXPORT_BLOCKED,
    EXPORT_INCOMPLETE,
    EXPORT_NOT_READY,
    EXPORT_REVIEW_REQUIRED,
    EXPORT_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_final_readiness_review_export_spec.report_writer import (
    render_xaman_governance_final_readiness_review_export_json,
    render_xaman_governance_final_readiness_review_export_markdown,
)

BASE = "tests/fixtures/xaman_governance_final_readiness_review_export_spec"


def _run(name):
    return build_xaman_governance_final_readiness_review_export_spec(
        load_xaman_governance_final_readiness_review_export_fixture(f"{BASE}/{name}")
    )


def test_phase76_complete_export_is_spec_review_ready_and_deterministic():
    first = _run("complete_spec_review_ready_export_package.json")
    second = _run("complete_spec_review_ready_export_package.json")
    assert first == second
    assert first.export_readiness_classification == EXPORT_SPEC_REVIEW_READY
    f = first.spec.safety_flags
    assert f.spec_only is True and f.review_export_spec_only is True
    assert f.runtime_export_service_allowed is False and f.download_service_allowed is False
    assert f.api_route_allowed is False and f.dashboard_ui_allowed is False


def test_phase76_missing_required_phase_artifacts_are_incomplete():
    for name in [
        "missing_phase75_final_bundle.json",
        "missing_phase70_support_artifact.json",
        "missing_phase71_support_artifact.json",
        "missing_phase72_support_artifact.json",
        "missing_phase73_support_artifact.json",
        "missing_phase74_support_artifact.json",
    ]:
        assert _run(name).export_readiness_classification == EXPORT_INCOMPLETE


def test_phase76_review_paths_preserve_limitations():
    for name in [
        "redacted_artifact_requiring_review.json",
        "reference_only_artifact_requiring_manual_verification.json",
        "unresolved_blocker_summary.json",
        "unresolved_limitation_summary.json",
        "expired_waiver_included.json",
        "revoked_waiver_included.json",
    ]:
        report = _run(name)
        assert report.export_readiness_classification in {EXPORT_REVIEW_REQUIRED, EXPORT_NOT_READY}
        assert report.spec.limitation_register


def test_phase76_blockers_fail_closed():
    for name in [
        "overdue_critical_sla_included.json",
        "unsafe_waiver_attempt_included.json",
        "blocked_due_xaman_payload_approval_wording.json",
        "blocked_due_wallet_material_approval_wording.json",
        "blocked_due_signing_submission_autofill_approval_wording.json",
        "blocked_due_testnet_live_execution_approval_wording.json",
        "blocked_due_runtime_export_service_marker.json",
        "blocked_due_download_service_marker.json",
        "blocked_due_api_ui_export_route_marker.json",
        "blocked_due_safety_bypass_marker.json",
    ]:
        report = _run(name)
        assert report.export_readiness_classification == EXPORT_BLOCKED
        assert report.blockers


def test_phase76_traceability_manifest_and_reports_are_stable():
    report = _run("complete_spec_review_ready_export_package.json")
    j = render_xaman_governance_final_readiness_review_export_json(report)
    m = render_xaman_governance_final_readiness_review_export_markdown(report)
    assert '"source_artifact_type": "PHASE75_FINAL_READINESS_BUNDLE_REPORT"' in j
    assert '"review_export_spec_only": true' in j
    assert '"manifest_id": "manifest-76-complete_spec_review_ready_export_package"' in j
    assert "Still no runtime export service." in m
    assert "Still no API/UI export route." in m
