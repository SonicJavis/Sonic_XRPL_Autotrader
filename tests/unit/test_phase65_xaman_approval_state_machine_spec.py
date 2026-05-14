from sonic_xrpl.xaman_approval_state_machine_spec import (
    build_xaman_approval_state_machine_spec,
    load_xaman_approval_state_machine_fixture,
)
from sonic_xrpl.xaman_approval_state_machine_spec.models import (
    INSUFFICIENT_EVIDENCE,
    SPEC_INVALID,
    SPEC_REVIEW_REQUIRED,
    SPEC_VALID,
    TRANSITION_BLOCKED,
)
from sonic_xrpl.xaman_approval_state_machine_spec.reporting import (
    render_xaman_approval_state_machine_spec_json,
    render_xaman_approval_state_machine_spec_markdown,
)


def _run(path: str):
    return build_xaman_approval_state_machine_spec(load_xaman_approval_state_machine_fixture(path))


def test_phase65_healthy_fixture_is_spec_valid():
    report = _run("tests/fixtures/xaman_approval_state_machine_spec/healthy_approval_state_machine_spec.json")
    assert report.outcome == SPEC_VALID
    flags = report.spec.safety_flags
    assert flags.state_machine_spec_only is True
    assert flags.runtime_state_machine_allowed is False
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


def test_phase65_missing_transitions_fail_closed():
    assert "missing_operator_approval_transition" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/missing_operator_approval_transition.json"
    ).validation_errors
    assert "missing_callback_verification_transition" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/missing_callback_verification_transition.json"
    ).validation_errors
    assert "missing_audit_required_transition" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/missing_audit_required_transition.json"
    ).validation_errors


def test_phase65_missing_controls_and_invalid_blocks_reported():
    assert "missing_idempotency_requirement" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/missing_idempotency_requirement.json"
    ).validation_errors
    assert "missing_ttl_replay_requirement" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/missing_ttl_replay_requirement.json"
    ).validation_errors
    assert "missing_invalid_direct_callback_to_final_block" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/invalid_direct_callback_to_final_transition.json"
    ).validation_errors
    assert "missing_invalid_duplicate_callback_accept_block" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/invalid_duplicate_callback_accepted_transition.json"
    ).validation_errors
    assert "missing_invalid_replay_accept_block" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/invalid_replay_accepted_transition.json"
    ).validation_errors
    assert "missing_invalid_expired_to_approved_block" in _run(
        "tests/fixtures/xaman_approval_state_machine_spec/invalid_expired_to_approved_transition.json"
    ).validation_errors


def test_phase65_unsafe_markers_transition_blocked():
    for name in [
        "attempted_payload_creation_transition.json",
        "attempted_xaman_api_transition.json",
        "attempted_signing_submission_transition.json",
        "attempted_wallet_material_transition.json",
        "attempted_runtime_state_machine_marker.json",
        "attempted_db_write_persistence_marker.json",
        "attempted_testnet_live_execution_marker.json",
    ]:
        report = _run(f"tests/fixtures/xaman_approval_state_machine_spec/{name}")
        assert report.outcome == TRANSITION_BLOCKED
        assert any(item.startswith("blocked_") for item in report.validation_errors)


def test_phase65_intermediate_outcomes_available():
    report = _run("tests/fixtures/xaman_approval_state_machine_spec/missing_operator_approval_transition.json")
    assert report.outcome in {SPEC_REVIEW_REQUIRED, SPEC_INVALID, INSUFFICIENT_EVIDENCE}


def test_phase65_reporting_outputs_include_state_machine_tables():
    report = _run("tests/fixtures/xaman_approval_state_machine_spec/healthy_approval_state_machine_spec.json")
    as_json = render_xaman_approval_state_machine_spec_json(report)
    as_md = render_xaman_approval_state_machine_spec_markdown(report)
    assert '"state_machine_spec_only": true' in as_json
    assert '"runtime_state_machine_allowed": false' in as_json
    assert "Phase 65 Xaman Approval State Machine Spec" in as_md
