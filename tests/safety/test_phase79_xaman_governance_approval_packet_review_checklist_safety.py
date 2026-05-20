from pathlib import Path
from sonic_xrpl.xaman_governance_approval_packet_review_checklist_spec import build_xaman_governance_approval_packet_review_checklist_spec,load_xaman_governance_approval_packet_review_checklist_fixture
BASE='tests/fixtures/xaman_governance_approval_packet_review_checklist_spec'
def _run(name): return build_xaman_governance_approval_packet_review_checklist_spec(load_xaman_governance_approval_packet_review_checklist_fixture(f'{BASE}/{name}'))
def test_phase79_module_has_no_network_wallet_archive_or_runtime_calls():
    combined='\n'.join(p.read_text(encoding='utf-8') for p in Path('src/sonic_xrpl/xaman_governance_approval_packet_review_checklist_spec').glob('*.py'))
    for token in ['requests.get(','requests.post(','http://','https://','submitAndWait','autofill(','Wallet(','fromSeed','sqlite3.connect(','session.commit(','zipfile','tarfile']:
        assert token not in combined
def test_phase79_flags_block_runtime_checklist_payload_execution_wallet_mutation_and_bypass():
    f=_run('complete_spec_review_ready_checklist.json').spec.safety_flags
    assert f.spec_only is True and f.review_checklist_spec_only is True and f.runtime_checklist_service_allowed is False and f.download_service_allowed is False and f.api_route_allowed is False and f.dashboard_ui_allowed is False and f.safety_bypass_allowed is False and f.testnet_execution_allowed is False and f.xaman_payload_creation_allowed is False and f.xaman_api_calls_allowed is False and f.xaman_sdk_dependency_allowed is False and f.signing_allowed is False and f.submission_allowed is False and f.autofill_allowed is False and f.wallet_material_allowed is False and f.live_execution_allowed is False and f.runtime_mutation_allowed is False
