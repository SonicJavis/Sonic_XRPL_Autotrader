from sonic_xrpl.xaman_manual_approval_spec import build_manual_approval_spec, load_manual_approval_spec_fixture
from sonic_xrpl.xaman_manual_approval_spec.reporting import (
    render_manual_approval_spec_json,
    render_manual_approval_spec_markdown,
)


def _run(path: str):
    return build_manual_approval_spec(load_manual_approval_spec_fixture(path))


def test_healthy_design_spec_fixture_is_valid():
    report = _run("tests/fixtures/xaman_manual_approval_spec/healthy_design_only.json")
    assert report.valid_design_spec is True
    assert report.spec.safety_flags.design_spec_only is True
    assert report.spec.safety_flags.payload_creation_allowed is False
    assert report.spec.safety_flags.signing_allowed is False
    assert report.spec.safety_flags.submission_allowed is False
    assert report.spec.safety_flags.live_execution_allowed is False


def test_missing_requirements_fail_validation():
    for fixture, marker in (
        ("tests/fixtures/xaman_manual_approval_spec/missing_risk_disclosure.json", "missing_risk_disclosure"),
        ("tests/fixtures/xaman_manual_approval_spec/missing_replay_protection.json", "missing_replay_protection"),
        ("tests/fixtures/xaman_manual_approval_spec/missing_expiry_ttl.json", "missing_approval_expiry_ttl"),
        ("tests/fixtures/xaman_manual_approval_spec/missing_audit_trail.json", "missing_audit_trail"),
    ):
        report = _run(fixture)
        assert report.valid_design_spec is False
        assert marker in report.validation_errors


def test_attempted_unsafe_markers_fail_closed():
    for fixture, marker in (
        ("tests/fixtures/xaman_manual_approval_spec/attempted_payload_creation_marker.json", "blocked_attempted_payload_creation"),
        ("tests/fixtures/xaman_manual_approval_spec/attempted_signing_marker.json", "blocked_attempted_signing"),
        ("tests/fixtures/xaman_manual_approval_spec/attempted_submission_marker.json", "blocked_attempted_submission"),
        ("tests/fixtures/xaman_manual_approval_spec/attempted_wallet_material_marker.json", "blocked_attempted_wallet_material"),
        ("tests/fixtures/xaman_manual_approval_spec/attempted_live_execution_marker.json", "blocked_attempted_live_execution"),
    ):
        report = _run(fixture)
        assert report.valid_design_spec is False
        assert marker in report.validation_errors


def test_future_testnet_and_mainnet_requests_are_blocked():
    testnet = _run("tests/fixtures/xaman_manual_approval_spec/future_testnet_candidate_blocked.json")
    mainnet = _run("tests/fixtures/xaman_manual_approval_spec/future_mainnet_candidate_blocked.json")
    assert "future_testnet_gate_blocked" in testnet.validation_errors
    assert "future_mainnet_gate_blocked" in mainnet.validation_errors
    assert testnet.spec.future_gates.testnet_implementation_allowed is False
    assert mainnet.spec.future_gates.mainnet_live_allowed is False


def test_report_outputs_include_design_only_markers():
    report = _run("tests/fixtures/xaman_manual_approval_spec/healthy_design_only.json")
    rendered_json = render_manual_approval_spec_json(report)
    rendered_md = render_manual_approval_spec_markdown(report)
    assert '"design_spec_only": true' in rendered_json
    assert '"payload_creation_allowed": false' in rendered_json
    assert "Phase 61 Xaman Manual Approval Design Spec" in rendered_md
