from pathlib import Path

from sonic_xrpl.xaman_manual_approval_spec import build_manual_approval_spec, load_manual_approval_spec_fixture


def _run(path: str):
    return build_manual_approval_spec(load_manual_approval_spec_fixture(path))


def test_phase61_module_has_no_live_or_sdk_tokens():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/xaman_manual_approval_spec").glob("*.py"))
    forbidden = [
        "xumm-sdk",
        "xaman-sdk",
        "requests.get(",
        "requests.post(",
        "websocket",
        "wss://",
        "https://",
        "submitAndWait",
        ".autofill(",
        "Wallet(",
        "fromSeed",
        "OfferCreate",
        "Payment",
        "TrustSet",
    ]
    for token in forbidden:
        assert token not in combined


def test_phase61_spec_flags_are_fail_closed():
    report = _run("tests/fixtures/xaman_manual_approval_spec/healthy_design_only.json")
    flags = report.spec.safety_flags
    assert flags.design_spec_only is True
    assert flags.manual_approval_required is True
    assert flags.payload_creation_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.autofill_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.live_execution_allowed is False
    assert flags.runtime_mutation_allowed is False


def test_phase61_attempt_markers_are_blocked():
    report = _run("tests/fixtures/xaman_manual_approval_spec/attempted_submission_marker.json")
    assert report.valid_design_spec is False
    assert "blocked_attempted_submission" in report.validation_errors
