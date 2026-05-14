from sonic_xrpl.xaman_audit_idempotency_spec import (
    build_xaman_audit_idempotency_spec,
    load_xaman_audit_idempotency_fixture,
)
from sonic_xrpl.xaman_audit_idempotency_spec.models import (
    INSUFFICIENT_EVIDENCE,
    SPEC_ACCEPTED,
    SPEC_REJECTED,
)
from sonic_xrpl.xaman_audit_idempotency_spec.reporting import (
    render_xaman_audit_idempotency_spec_json,
    render_xaman_audit_idempotency_spec_markdown,
)


def _run(path: str):
    return build_xaman_audit_idempotency_spec(load_xaman_audit_idempotency_fixture(path))


def test_phase64_healthy_fixture_is_spec_accepted():
    report = _run("tests/fixtures/xaman_audit_idempotency_spec/healthy_audit_idempotency_spec.json")
    assert report.outcome == SPEC_ACCEPTED
    flags = report.spec.safety_flags
    assert flags.audit_spec_only is True
    assert flags.idempotency_spec_only is True
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


def test_phase64_missing_requirements_fail_closed():
    assert "missing_correlation_id" in _run(
        "tests/fixtures/xaman_audit_idempotency_spec/missing_correlation_id.json"
    ).validation_errors
    assert "missing_idempotency_key_rule" in _run(
        "tests/fixtures/xaman_audit_idempotency_spec/missing_idempotency_key_rule.json"
    ).validation_errors
    assert "missing_payload_uuid_binding" in _run(
        "tests/fixtures/xaman_audit_idempotency_spec/missing_payload_uuid_binding.json"
    ).validation_errors
    assert "missing_operator_approval_binding" in _run(
        "tests/fixtures/xaman_audit_idempotency_spec/missing_operator_approval_binding.json"
    ).validation_errors
    assert "missing_replay_policy" in _run(
        "tests/fixtures/xaman_audit_idempotency_spec/missing_replay_policy.json"
    ).validation_errors
    assert "missing_duplicate_callback_policy" in _run(
        "tests/fixtures/xaman_audit_idempotency_spec/missing_duplicate_callback_policy.json"
    ).validation_errors


def test_phase64_audit_trail_requirements_missing_reported():
    assert "missing_append_only_requirement" in _run(
        "tests/fixtures/xaman_audit_idempotency_spec/missing_append_only_requirement.json"
    ).validation_errors
    assert "missing_tamper_evidence_requirement" in _run(
        "tests/fixtures/xaman_audit_idempotency_spec/missing_tamper_evidence_requirement.json"
    ).validation_errors
    report = _run("tests/fixtures/xaman_audit_idempotency_spec/missing_redaction_or_sensitive_exclusion.json")
    assert "missing_redaction_policy" in report.validation_errors
    assert "missing_sensitive_material_exclusion" in report.validation_errors


def test_phase64_attempted_unsafe_markers_are_spec_rejected():
    blocked_cases = [
        "attempted_database_write_marker.json",
        "attempted_persistence_implementation_marker.json",
        "attempted_callback_handler_marker.json",
        "attempted_xaman_api_marker.json",
        "attempted_payload_creation_marker.json",
        "attempted_signing_or_submission_marker.json",
        "attempted_wallet_material_marker.json",
        "attempted_testnet_live_execution_marker.json",
    ]
    for name in blocked_cases:
        report = _run(f"tests/fixtures/xaman_audit_idempotency_spec/{name}")
        assert report.outcome == SPEC_REJECTED
        assert any(item.startswith("blocked_") for item in report.validation_errors)


def test_phase64_insufficient_evidence_outcome_available():
    report = _run("tests/fixtures/xaman_audit_idempotency_spec/missing_redaction_or_sensitive_exclusion.json")
    assert report.outcome in {INSUFFICIENT_EVIDENCE, "SPEC_REVIEW_REQUIRED"}


def test_phase64_reporting_outputs_include_design_flags():
    report = _run("tests/fixtures/xaman_audit_idempotency_spec/healthy_audit_idempotency_spec.json")
    as_json = render_xaman_audit_idempotency_spec_json(report)
    as_md = render_xaman_audit_idempotency_spec_markdown(report)
    assert '"audit_spec_only": true' in as_json
    assert '"database_writes_allowed": false' in as_json
    assert "Phase 64 Xaman Audit Idempotency Spec" in as_md
