from pathlib import Path

from sonic_xrpl.xaman_governance_evidence_attestation_spec import (
    build_xaman_governance_evidence_attestation_spec,
    load_xaman_governance_evidence_attestation_fixture,
)


def _run(path: str):
    return build_xaman_governance_evidence_attestation_spec(
        load_xaman_governance_evidence_attestation_fixture(path)
    )


def test_phase71_module_has_no_network_wallet_or_execution_calls():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/sonic_xrpl/xaman_governance_evidence_attestation_spec").glob("*.py")
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


def test_phase71_flags_block_payload_wallet_testnet_live():
    report = _run(
        "tests/fixtures/xaman_governance_evidence_attestation_spec/complete_spec_review_ready_bundle.json"
    )
    f = report.spec.safety_flags
    assert f.spec_only is True
    assert f.attestation_only is True
    assert f.testnet_execution_allowed is False
    assert f.xaman_payload_creation_allowed is False
    assert f.xaman_api_calls_allowed is False
    assert f.xaman_sdk_dependency_allowed is False
    assert f.signing_allowed is False
    assert f.submission_allowed is False
    assert f.autofill_allowed is False
    assert f.wallet_material_allowed is False
    assert f.live_execution_allowed is False
    assert f.runtime_mutation_allowed is False
