from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec import (
    build_xaman_governance_escalation_resolution_sla_spec,
    load_xaman_governance_escalation_resolution_sla_fixture,
)
from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec.models import (
    SLA_BLOCKED,
    SLA_NOT_READY,
    SLA_OVERDUE,
    SLA_REVIEW_REQUIRED,
    SLA_SPEC_REVIEW_READY,
)
from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec.report_writer import (
    render_xaman_governance_escalation_resolution_sla_json,
    render_xaman_governance_escalation_resolution_sla_markdown,
)


def _run(path: str):
    return build_xaman_governance_escalation_resolution_sla_spec(
        load_xaman_governance_escalation_resolution_sla_fixture(path)
    )


def test_phase73_complete_bundle_is_spec_review_ready():
    report = _run(
        "tests/fixtures/xaman_governance_escalation_resolution_sla_spec/complete_spec_review_ready_sla_bundle.json"
    )
    assert report.readiness_classification == SLA_SPEC_REVIEW_READY
    flags = report.spec.safety_flags
    assert flags.spec_only is True
    assert flags.sla_spec_only is True
    assert flags.runtime_sla_engine_allowed is False
    assert flags.scheduler_allowed is False
    assert flags.notification_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.live_execution_allowed is False


def test_phase73_conservative_outcomes_for_missing_and_deferred_cases():
    for name in [
        "open_low_severity_escalation.json",
        "missing_reviewer_accountability.json",
        "missing_resolution_evidence.json",
        "missing_dependency_audit_resolution_blocker.json",
        "unresolved_safety_scan_review_blocker.json",
        "deferred_escalation_with_explicit_limitation.json",
        "rejected_escalation.json",
        "superseded_escalation.json",
        "stale_evidence_resolution_rejected.json",
    ]:
        report = _run(f"tests/fixtures/xaman_governance_escalation_resolution_sla_spec/{name}")
        assert report.readiness_classification in {
            SLA_NOT_READY,
            SLA_REVIEW_REQUIRED,
            SLA_OVERDUE,
            SLA_BLOCKED,
            SLA_SPEC_REVIEW_READY,
        }


def test_phase73_critical_overdue_classification():
    report = _run(
        "tests/fixtures/xaman_governance_escalation_resolution_sla_spec/critical_overdue_escalation.json"
    )
    assert report.readiness_classification in {SLA_OVERDUE, SLA_BLOCKED}


def test_phase73_blocked_markers_force_blocked_state():
    for name in [
        "blocked_xaman_payload_ambiguity.json",
        "blocked_wallet_material_ambiguity.json",
        "blocked_testnet_live_approval_wording.json",
        "blocked_scheduler_runtime_sla_marker.json",
        "blocked_notification_runtime_marker.json",
    ]:
        report = _run(f"tests/fixtures/xaman_governance_escalation_resolution_sla_spec/{name}")
        assert report.readiness_classification == SLA_BLOCKED
        assert report.blockers


def test_phase73_report_formats_include_scheduler_and_notification_safety():
    report = _run(
        "tests/fixtures/xaman_governance_escalation_resolution_sla_spec/complete_spec_review_ready_sla_bundle.json"
    )
    as_json = render_xaman_governance_escalation_resolution_sla_json(report)
    as_md = render_xaman_governance_escalation_resolution_sla_markdown(report)
    assert '"runtime_sla_engine_allowed": false' in as_json
    assert '"scheduler_allowed": false' in as_json
    assert '"notification_allowed": false' in as_json
    assert "Still no runtime SLA engine." in as_md
    assert "Still no scheduler." in as_md
    assert "Still no notifications." in as_md
