from pathlib import Path
from sonic_xrpl.xaman_governance_final_readiness_bundle_spec import build_xaman_governance_final_readiness_bundle_spec, load_xaman_governance_final_readiness_bundle_fixture
BASE="tests/fixtures/xaman_governance_final_readiness_bundle_spec"
def _run(name): return build_xaman_governance_final_readiness_bundle_spec(load_xaman_governance_final_readiness_bundle_fixture(f"{BASE}/{name}"))
def test_phase75_module_has_no_network_wallet_or_runtime_calls():
    combined="\n".join(p.read_text(encoding="utf-8") for p in Path("src/sonic_xrpl/xaman_governance_final_readiness_bundle_spec").glob("*.py"))
    for token in ["requests.get(","requests.post(","http://","https://","submitAndWait","autofill(","Wallet(","fromSeed","sqlite3.connect(","session.commit("]:
        assert token not in combined

def test_phase75_flags_block_payload_execution_wallet_mutation_and_bypass():
    f=_run("complete_spec_review_ready_final_bundle.json").spec.safety_flags
    assert f.spec_only is True
    assert f.final_readiness_bundle_spec_only is True
    assert f.runtime_readiness_service_allowed is False
    assert f.safety_bypass_allowed is False
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
