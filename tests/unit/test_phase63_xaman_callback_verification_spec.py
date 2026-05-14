from sonic_xrpl.xaman_callback_verification_spec import (
    build_xaman_callback_verification_spec,
    load_xaman_callback_verification_fixture,
)
from sonic_xrpl.xaman_callback_verification_spec.reporting import (
    render_xaman_callback_verification_spec_json,
    render_xaman_callback_verification_spec_markdown,
)
from sonic_xrpl.xaman_callback_verification_spec.threat_model import (
    render_phase63_blocker_register,
    render_phase63_threat_model,
)


def _run(path: str):
    return build_xaman_callback_verification_spec(load_xaman_callback_verification_fixture(path))


def test_phase63_healthy_fixture_is_valid():
    report = _run("tests/fixtures/xaman_callback_verification_spec/healthy_callback_spec.json")
    assert report.valid_design_spec is True
    assert report.spec.safety_flags.callback_spec_only is True
    assert report.spec.safety_flags.verification_design_only is True
    assert report.spec.safety_flags.runtime_callback_handler_allowed is False
    assert report.spec.safety_flags.webhook_runtime_allowed is False
    assert report.spec.safety_flags.payload_creation_allowed is False
    assert report.spec.safety_flags.xaman_api_calls_allowed is False
    assert report.spec.safety_flags.testnet_execution_allowed is False
    assert report.spec.safety_flags.live_execution_allowed is False


def test_phase63_missing_requirements_fail_closed():
    assert "missing_authenticity_requirement" in _run(
        "tests/fixtures/xaman_callback_verification_spec/missing_authenticity.json"
    ).validation_errors
    assert "missing_nonce_requirement" in _run(
        "tests/fixtures/xaman_callback_verification_spec/missing_nonce_requirement.json"
    ).validation_errors
    assert "missing_ttl_requirement" in _run(
        "tests/fixtures/xaman_callback_verification_spec/missing_ttl_requirement.json"
    ).validation_errors
    assert "missing_idempotency_requirement" in _run(
        "tests/fixtures/xaman_callback_verification_spec/missing_idempotency.json"
    ).validation_errors
    assert "missing_audit_trail_requirement" in _run(
        "tests/fixtures/xaman_callback_verification_spec/missing_audit_trail.json"
    ).validation_errors


def test_phase63_replay_duplicate_and_gate_failures_are_reported():
    assert "missing_replay_window_seconds" in _run(
        "tests/fixtures/xaman_callback_verification_spec/replay_window_incomplete.json"
    ).validation_errors
    assert "missing_duplicate_callback_handling" in _run(
        "tests/fixtures/xaman_callback_verification_spec/duplicate_callback_incomplete.json"
    ).validation_errors
    assert "incomplete_testnet_gate" in _run(
        "tests/fixtures/xaman_callback_verification_spec/future_testnet_gate_incomplete.json"
    ).validation_errors
    assert "live_gate_not_blocked" in _run(
        "tests/fixtures/xaman_callback_verification_spec/future_live_gate_blocked.json"
    ).validation_errors


def test_phase63_attempted_runtime_actions_fail_closed():
    assert "blocked_attempted_callback_handler" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_callback_handler.json"
    ).validation_errors
    assert "blocked_attempted_webhook_runtime" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_webhook_runtime.json"
    ).validation_errors
    assert "blocked_attempted_xaman_api_call" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_api_call.json"
    ).validation_errors
    assert "blocked_attempted_payload_creation" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_payload_creation.json"
    ).validation_errors
    assert "blocked_attempted_signing" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_signing.json"
    ).validation_errors
    assert "blocked_attempted_submission" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_submission.json"
    ).validation_errors
    assert "blocked_attempted_wallet_material" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_wallet_material.json"
    ).validation_errors


def test_phase63_reporting_and_threat_model_outputs_are_design_only():
    report = _run("tests/fixtures/xaman_callback_verification_spec/healthy_callback_spec.json")
    as_json = render_xaman_callback_verification_spec_json(report)
    as_md = render_xaman_callback_verification_spec_markdown(report)
    threat = render_phase63_threat_model(report)
    blockers = render_phase63_blocker_register(report)

    assert '"callback_spec_only": true' in as_json
    assert '"runtime_callback_handler_allowed": false' in as_json
    assert "Phase 63 Xaman Callback Verification Spec" in as_md
    assert threat["design_only"] is True
    assert threat["webhook_runtime_allowed"] is False
    assert len(blockers) >= 6
