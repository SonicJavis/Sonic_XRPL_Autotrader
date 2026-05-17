from pathlib import Path

from sonic_xrpl.xaman_governance_exception_waiver_register_spec import (
    build_xaman_governance_exception_waiver_register_spec,
    load_xaman_governance_exception_waiver_register_fixture,
)

BASE = "tests/fixtures/xaman_governance_exception_waiver_register_spec"

def _run(name: str):
    return build_xaman_governance_exception_waiver_register_spec(
        load_xaman_governance_exception_waiver_register_fixture(f"{BASE}/{name}")
    )

def test_phase74_module_has_no_network_wallet_or_runtime_calls():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/sonic_xrpl/xaman_governance_exception_waiver_register_spec").glob("*.py")
    )
    forbidden = [
        "requests.get(",
        "requests.post(",
        "http://",
        "https://",
        "submitAndWait",
        "autofill(",
        "Wallet(",
        "fromSeed",
        "sqlite3.connect(",
        "session.commit(",
    ]
    for token in forbidden:
        assert token not in combined

def test_phase74_flags_block_payload_execution_wallet_mutation_and_bypass():
    report = _run("complete_spec_review_ready_waiver_register.json")
    flags = report.spec.safety_flags
    assert flags.spec_only is True
    assert flags.waiver_register_spec_only is True
    assert flags.runtime_waiver_service_allowed is False
    assert flags.safety_bypass_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.xaman_payload_creation_allowed is False
    assert flags.xaman_api_calls_allowed is False
    assert flags.xaman_sdk_dependency_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.autofill_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.live_execution_allowed is False
    assert flags.runtime_mutation_allowed is False
