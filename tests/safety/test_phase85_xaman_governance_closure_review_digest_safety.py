from pathlib import Path
from sonic_xrpl.xaman_governance_closure_review_digest_spec import build_xaman_governance_closure_review_digest_spec,load_xaman_governance_closure_review_digest_fixture
BASE='tests/fixtures/xaman_governance_closure_review_digest_spec'
def _run(name): return build_xaman_governance_closure_review_digest_spec(load_xaman_governance_closure_review_digest_fixture(f'{BASE}/{name}'))
def test_phase85_module_has_no_network_wallet_archive_or_runtime_calls():
    combined='\n'.join(p.read_text(encoding='utf-8') for p in Path('src/sonic_xrpl/xaman_governance_closure_review_digest_spec').glob('*.py'))
    for t in ['requests.get(','requests.post(','http://','https://','submitAndWait','autofill(','Wallet(','fromSeed','sqlite3.connect(','session.commit(','zipfile','tarfile']:
        assert t not in combined
def test_phase85_flags_block_runtime_closure_digest_payload_execution_wallet_mutation_and_bypass():
    f=_run('complete_spec_review_ready_closure_digest.json').spec.safety_flags
    assert f.spec_only and f.closure_review_digest_spec_only and (not f.runtime_closure_digest_service_allowed) and (not f.download_service_allowed) and (not f.api_route_allowed) and (not f.dashboard_ui_allowed) and (not f.safety_bypass_allowed) and (not f.testnet_execution_allowed) and (not f.xaman_payload_creation_allowed) and (not f.xaman_api_calls_allowed) and (not f.xaman_sdk_dependency_allowed) and (not f.signing_allowed) and (not f.submission_allowed) and (not f.autofill_allowed) and (not f.wallet_material_allowed) and (not f.live_execution_allowed) and (not f.runtime_mutation_allowed)
