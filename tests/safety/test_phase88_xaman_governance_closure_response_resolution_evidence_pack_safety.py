from pathlib import Path
from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec import build_xaman_governance_closure_response_resolution_evidence_pack_spec,load_xaman_governance_closure_response_resolution_evidence_pack_fixture

BASE='tests/fixtures/xaman_governance_closure_response_resolution_evidence_pack_spec'
def _run(name): return build_xaman_governance_closure_response_resolution_evidence_pack_spec(load_xaman_governance_closure_response_resolution_evidence_pack_fixture(f'{BASE}/{name}'))

def test_phase88_module_has_no_network_wallet_archive_or_runtime_calls():
    combined='\n'.join(path.read_text(encoding='utf-8') for path in Path('src/sonic_xrpl/xaman_governance_closure_response_resolution_evidence_pack_spec').glob('*.py'))
    for token in ['requests.get(','requests.post(','http://','https://','submitAndWait','autofill(','Wallet(','fromSeed','sqlite3.connect(','session.commit(','zipfile','tarfile']:
        assert token not in combined

def test_phase88_flags_block_runtime_evidence_pack_payload_execution_wallet_mutation_and_bypass():
    flags=_run('complete_spec_review_ready_evidence_pack.json').spec.safety_flags
    assert flags.spec_only and flags.closure_response_resolution_evidence_pack_spec_only and not flags.runtime_closure_response_resolution_evidence_pack_service_allowed and not flags.download_service_allowed and not flags.api_route_allowed and not flags.dashboard_ui_allowed and not flags.safety_bypass_allowed and not flags.testnet_execution_allowed and not flags.xaman_payload_creation_allowed and not flags.xaman_api_calls_allowed and not flags.xaman_sdk_dependency_allowed and not flags.signing_allowed and not flags.submission_allowed and not flags.autofill_allowed and not flags.wallet_material_allowed and not flags.live_execution_allowed and not flags.runtime_mutation_allowed
