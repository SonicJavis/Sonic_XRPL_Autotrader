from sonic_xrpl.xaman_testnet_payload_spec import (
    build_xaman_testnet_payload_spec,
    load_xaman_testnet_payload_fixture,
)
from sonic_xrpl.xaman_testnet_payload_spec.reporting import (
    render_xaman_testnet_payload_spec_json,
    render_xaman_testnet_payload_spec_markdown,
)


def _run(path: str):
    return build_xaman_testnet_payload_spec(load_xaman_testnet_payload_fixture(path))


def test_phase62_healthy_fixture_is_valid():
    report = _run("tests/fixtures/xaman_testnet_payload_spec/healthy_design_review.json")
    assert report.valid_design_spec is True
    assert report.spec.safety_flags.design_spec_only is True
    assert report.spec.safety_flags.payload_creation_allowed is False
    assert report.spec.safety_flags.xaman_api_calls_allowed is False
    assert report.spec.safety_flags.live_execution_allowed is False


def test_phase62_missing_required_fields_fail_closed():
    assert "missing_nonce" in _run("tests/fixtures/xaman_testnet_payload_spec/missing_nonce.json").validation_errors
    assert "missing_payload_ttl" in _run("tests/fixtures/xaman_testnet_payload_spec/missing_ttl.json").validation_errors
    assert "missing_callback_signature" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/missing_callback_signature.json"
    ).validation_errors


def test_phase62_mainnet_is_blocked():
    report = _run("tests/fixtures/xaman_testnet_payload_spec/mainnet_blocked.json")
    assert "invalid_or_blocked_network" in report.validation_errors
    assert report.spec.testnet_gate.mainnet_blocked is True


def test_phase62_attempted_unsafe_actions_fail_closed():
    assert "blocked_attempted_payload_creation" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/attempted_payload_creation.json"
    ).validation_errors
    assert "blocked_attempted_signing" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/attempted_signing.json"
    ).validation_errors
    assert "blocked_attempted_submission" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/attempted_submission.json"
    ).validation_errors
    assert "blocked_attempted_xaman_api_call" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/attempted_api_call.json"
    ).validation_errors
    assert "blocked_attempted_wallet_material" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/attempted_wallet_material.json"
    ).validation_errors


def test_phase62_reporting_is_design_only():
    report = _run("tests/fixtures/xaman_testnet_payload_spec/healthy_design_review.json")
    as_json = render_xaman_testnet_payload_spec_json(report)
    as_md = render_xaman_testnet_payload_spec_markdown(report)
    assert '"payload_creation_allowed": false' in as_json
    assert '"xaman_api_calls_allowed": false' in as_json
    assert "Phase 62 Xaman Testnet Payload Schema Review" in as_md
