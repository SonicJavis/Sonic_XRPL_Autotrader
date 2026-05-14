from pathlib import Path

from sonic_xrpl.xaman_callback_verification_spec import (
    build_xaman_callback_verification_spec,
    load_xaman_callback_verification_fixture,
)


def _run(path: str):
    return build_xaman_callback_verification_spec(load_xaman_callback_verification_fixture(path))


def test_phase63_module_has_no_runtime_callback_or_network_usage():
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/xaman_callback_verification_spec").glob("*.py")
    )
    forbidden = [
        "FastAPI(",
        "@app.post",
        "requests.get(",
        "requests.post(",
        "http://",
        "https://",
        "websocket",
        "submitAndWait",
        "fromSeed",
        "Wallet(",
        "OfferCreate",
        "Payment",
        "TrustSet",
    ]
    for token in forbidden:
        assert token not in combined


def test_phase63_flags_and_gates_are_fail_closed():
    report = _run("tests/fixtures/xaman_callback_verification_spec/healthy_callback_spec.json")
    flags = report.spec.safety_flags
    assert flags.callback_spec_only is True
    assert flags.verification_design_only is True
    assert flags.runtime_callback_handler_allowed is False
    assert flags.webhook_runtime_allowed is False
    assert flags.payload_creation_allowed is False
    assert flags.xaman_api_calls_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.autofill_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.live_execution_allowed is False


def test_phase63_attempted_actions_and_gate_failures_blocked():
    assert "blocked_attempted_live_execution" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_live_execution.json"
    ).validation_errors
    assert "blocked_attempted_testnet_execution" in _run(
        "tests/fixtures/xaman_callback_verification_spec/attempted_testnet_execution.json"
    ).validation_errors
    assert "incomplete_testnet_gate" in _run(
        "tests/fixtures/xaman_callback_verification_spec/future_testnet_gate_incomplete.json"
    ).validation_errors
