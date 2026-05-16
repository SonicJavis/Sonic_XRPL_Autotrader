from sonic_xrpl.xaman_dry_run_readiness_review_spec import (
    build_xaman_dry_run_readiness_spec,
    load_xaman_dry_run_readiness_fixture,
)
from sonic_xrpl.xaman_dry_run_readiness_review_spec.models import (
    INSUFFICIENT_EVIDENCE,
    READINESS_BLOCKED,
    READINESS_SPEC_INVALID,
    READINESS_SPEC_REVIEW_REQUIRED,
    READINESS_SPEC_VALID,
)
from sonic_xrpl.xaman_dry_run_readiness_review_spec.reporting import (
    render_xaman_dry_run_readiness_json,
    render_xaman_dry_run_readiness_markdown,
)


def _run(path: str):
    return build_xaman_dry_run_readiness_spec(
        load_xaman_dry_run_readiness_fixture(path)
    )


def test_phase69_healthy_fixture_is_valid():
    report = _run(
        "tests/fixtures/xaman_dry_run_readiness_review_spec/healthy_readiness_review_pack.json"
    )
    assert report.outcome == READINESS_SPEC_VALID
    flags = report.spec.safety_flags
    assert flags.dry_run_readiness_spec_only is True
    assert flags.runtime_dry_run_runner_allowed is False
    assert flags.runtime_checklist_runner_allowed is False
    assert flags.export_implementation_allowed is False
    assert flags.file_write_allowed is False
    assert flags.ui_implementation_allowed is False
    assert flags.api_route_allowed is False
    assert flags.runtime_service_allowed is False
    assert flags.persistence_implementation_allowed is False
    assert flags.database_writes_allowed is False
    assert flags.callback_handler_allowed is False
    assert flags.webhook_runtime_allowed is False
    assert flags.payload_creation_allowed is False
    assert flags.xaman_api_calls_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.live_execution_allowed is False


def test_phase69_missing_required_references_and_gates_fail_closed():
    for name, error in [
        ("missing_manual_approval_design_reference.json", "missing_manual_approval_design_reference"),
        ("missing_payload_schema_spec_reference.json", "missing_payload_schema_spec_reference"),
        ("missing_callback_verification_spec_reference.json", "missing_callback_verification_spec_reference"),
        ("missing_audit_idempotency_spec_reference.json", "missing_audit_idempotency_spec_reference"),
        ("missing_approval_state_machine_spec_reference.json", "missing_approval_state_machine_spec_reference"),
        ("missing_operator_consent_ux_reference.json", "missing_operator_consent_ux_reference"),
        ("missing_consent_evidence_pack_reference.json", "missing_consent_evidence_pack_reference"),
        ("missing_preflight_safety_checklist_reference.json", "missing_preflight_safety_checklist_reference"),
        ("missing_dependency_audit_status.json", "missing_dependency_audit_status"),
        ("missing_safety_grep_status.json", "missing_safety_grep_status"),
        ("missing_audit_validator_status.json", "missing_audit_validator_status"),
        ("missing_migration_safe_status.json", "missing_migration_safe_status"),
        ("missing_guard_critical_status.json", "missing_guard_critical_status"),
        ("missing_no_secrets_status.json", "missing_no_secrets_status"),
        ("missing_no_wallet_material_status.json", "missing_no_wallet_material_status"),
        ("missing_no_xaman_api_status.json", "missing_no_xaman_api_status"),
        ("missing_no_payload_created_status.json", "missing_no_payload_created_status"),
        ("missing_no_signing_submission_status.json", "missing_no_signing_submission_status"),
        ("missing_no_testnet_execution_status.json", "missing_no_testnet_execution_status"),
        ("missing_no_live_execution_status.json", "missing_no_live_execution_status"),
        ("missing_rollback_plan.json", "missing_rollback_plan_status"),
        ("missing_kill_switch_design.json", "missing_kill_switch_design_status"),
    ]:
        report = _run(f"tests/fixtures/xaman_dry_run_readiness_review_spec/{name}")
        assert error in report.validation_errors


def test_phase69_unsafe_markers_are_blocked():
    for name in [
        "invalid_payload_created_marker.json",
        "invalid_xaman_called_marker.json",
        "invalid_signing_submission_marker.json",
        "invalid_wallet_material_marker.json",
        "invalid_runtime_runner_marker.json",
        "invalid_ui_api_runtime_marker.json",
        "invalid_export_file_write_marker.json",
        "invalid_persistence_db_write_marker.json",
        "invalid_testnet_live_execution_marker.json",
        "invalid_testnet_approved_marker.json",
        "invalid_live_approved_marker.json",
    ]:
        report = _run(f"tests/fixtures/xaman_dry_run_readiness_review_spec/{name}")
        assert report.outcome == READINESS_BLOCKED
        assert any(item.startswith("blocked_") for item in report.validation_errors)


def test_phase69_intermediate_outcomes_available():
    report = _run(
        "tests/fixtures/xaman_dry_run_readiness_review_spec/missing_manual_approval_design_reference.json"
    )
    assert report.outcome in {
        READINESS_SPEC_REVIEW_REQUIRED,
        READINESS_SPEC_INVALID,
        INSUFFICIENT_EVIDENCE,
    }


def test_phase69_reporting_includes_required_sections():
    report = _run(
        "tests/fixtures/xaman_dry_run_readiness_review_spec/healthy_readiness_review_pack.json"
    )
    as_json = render_xaman_dry_run_readiness_json(report)
    as_md = render_xaman_dry_run_readiness_markdown(report)
    assert '"dry_run_readiness_spec_only": true' in as_json
    assert '"runtime_dry_run_runner_allowed": false' in as_json
    assert "Phase 69 Xaman Dry-Run Readiness Review Spec" in as_md
