from sonic_xrpl.xaman_preflight_safety_checklist_spec import (
    build_xaman_preflight_safety_checklist_spec,
    load_xaman_preflight_safety_checklist_fixture,
)
from sonic_xrpl.xaman_preflight_safety_checklist_spec.models import (
    INSUFFICIENT_EVIDENCE,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_SPEC_INVALID,
    PREFLIGHT_SPEC_REVIEW_REQUIRED,
    PREFLIGHT_SPEC_VALID,
)
from sonic_xrpl.xaman_preflight_safety_checklist_spec.reporting import (
    render_xaman_preflight_safety_checklist_json,
    render_xaman_preflight_safety_checklist_markdown,
)


def _run(path: str):
    return build_xaman_preflight_safety_checklist_spec(
        load_xaman_preflight_safety_checklist_fixture(path)
    )


def test_phase68_healthy_fixture_is_valid():
    report = _run(
        "tests/fixtures/xaman_preflight_safety_checklist_spec/healthy_preflight_checklist_spec.json"
    )
    assert report.outcome == PREFLIGHT_SPEC_VALID
    flags = report.spec.safety_flags
    assert flags.preflight_spec_only is True
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


def test_phase68_missing_required_gates_fail_closed():
    for name, error in [
        ("missing_evidence_pack_gate.json", "missing_evidence_pack_gate"),
        ("missing_payload_schema_gate.json", "missing_payload_schema_gate"),
        ("missing_callback_verification_gate.json", "missing_callback_verification_gate"),
        ("missing_audit_idempotency_gate.json", "missing_audit_idempotency_gate"),
        ("missing_approval_state_machine_gate.json", "missing_approval_state_machine_gate"),
        ("missing_operator_consent_ux_gate.json", "missing_operator_consent_ux_gate"),
        ("missing_dependency_audit_gate.json", "missing_dependency_audit_gate"),
        ("missing_safety_grep_gate.json", "missing_safety_grep_gate"),
        ("missing_audit_validator_gate.json", "missing_audit_validator_gate"),
        ("missing_migration_safe_gate.json", "missing_migration_safe_gate"),
        ("missing_guard_critical_gate.json", "missing_guard_critical_gate"),
        ("missing_no_secrets_gate.json", "missing_no_secrets_gate"),
        ("missing_no_wallet_material_gate.json", "missing_no_wallet_material_gate"),
        ("missing_no_xaman_api_gate.json", "missing_no_xaman_api_gate"),
        ("missing_no_payload_created_gate.json", "missing_no_payload_created_gate"),
        ("missing_no_signing_submission_gate.json", "missing_no_signing_submission_gate"),
        ("missing_no_testnet_execution_gate.json", "missing_no_testnet_execution_gate"),
        ("missing_no_live_execution_gate.json", "missing_no_live_execution_gate"),
        ("missing_rollback_plan.json", "missing_rollback_plan"),
        ("missing_kill_switch_design.json", "missing_kill_switch_design"),
    ]:
        report = _run(f"tests/fixtures/xaman_preflight_safety_checklist_spec/{name}")
        assert error in report.validation_errors


def test_phase68_unsafe_markers_are_blocked():
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
    ]:
        report = _run(f"tests/fixtures/xaman_preflight_safety_checklist_spec/{name}")
        assert report.outcome == PREFLIGHT_BLOCKED
        assert any(item.startswith("blocked_") for item in report.validation_errors)


def test_phase68_intermediate_outcomes_available():
    report = _run(
        "tests/fixtures/xaman_preflight_safety_checklist_spec/missing_evidence_pack_gate.json"
    )
    assert report.outcome in {
        PREFLIGHT_SPEC_REVIEW_REQUIRED,
        PREFLIGHT_SPEC_INVALID,
        INSUFFICIENT_EVIDENCE,
    }


def test_phase68_reporting_includes_required_sections():
    report = _run(
        "tests/fixtures/xaman_preflight_safety_checklist_spec/healthy_preflight_checklist_spec.json"
    )
    as_json = render_xaman_preflight_safety_checklist_json(report)
    as_md = render_xaman_preflight_safety_checklist_markdown(report)
    assert '"preflight_spec_only": true' in as_json
    assert '"runtime_checklist_runner_allowed": false' in as_json
    assert "Phase 68 Xaman Preflight Safety Checklist Spec" in as_md
