from pathlib import Path

from sonic_xrpl.xaman_testnet_payload_spec import build_xaman_testnet_payload_spec, load_xaman_testnet_payload_fixture


def _run(path: str):
    return build_xaman_testnet_payload_spec(load_xaman_testnet_payload_fixture(path))


def test_phase62_module_has_no_live_or_sdk_usage():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/xaman_testnet_payload_spec").glob("*.py"))
    forbidden = [
        "requests.get(",
        "requests.post(",
        "wss://",
        "https://",
        "submitAndWait",
        "fromSeed",
        "Wallet(",
        "OfferCreate",
        "Payment",
        "TrustSet",
    ]
    for token in forbidden:
        assert token not in combined


def test_phase62_flags_are_fail_closed():
    report = _run("tests/fixtures/xaman_testnet_payload_spec/healthy_design_review.json")
    flags = report.spec.safety_flags
    assert flags.design_spec_only is True
    assert flags.payload_creation_allowed is False
    assert flags.xaman_api_calls_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.autofill_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.live_execution_allowed is False


def test_phase62_mainnet_and_actions_blocked():
    assert "invalid_or_blocked_network" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/mainnet_blocked.json"
    ).validation_errors
    assert "blocked_attempted_xaman_api_call" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/attempted_api_call.json"
    ).validation_errors
    assert "blocked_attempted_live_execution" in _run(
        "tests/fixtures/xaman_testnet_payload_spec/attempted_live_execution.json"
    ).validation_errors
