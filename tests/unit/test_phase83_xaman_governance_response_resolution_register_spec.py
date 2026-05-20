from sonic_xrpl.xaman_governance_response_resolution_register_spec import build_xaman_governance_response_resolution_register_spec,load_xaman_governance_response_resolution_register_fixture
from sonic_xrpl.xaman_governance_response_resolution_register_spec.models import RESOLUTION_REGISTER_BLOCKED,RESOLUTION_REGISTER_INCOMPLETE,RESOLUTION_REGISTER_NOT_READY,RESOLUTION_REGISTER_REVIEW_REQUIRED,RESOLUTION_REGISTER_SPEC_REVIEW_READY
from sonic_xrpl.xaman_governance_response_resolution_register_spec.report_writer import render_xaman_governance_response_resolution_register_json,render_xaman_governance_response_resolution_register_markdown
BASE='tests/fixtures/xaman_governance_response_resolution_register_spec'
def _run(name): return build_xaman_governance_response_resolution_register_spec(load_xaman_governance_response_resolution_register_fixture(f'{BASE}/{name}'))

def test_phase83_complete_resolution_register_is_spec_review_ready_and_deterministic():
    first=_run('complete_spec_review_ready_resolution_register.json'); second=_run('complete_spec_review_ready_resolution_register.json')
    assert first==second; assert first.final_resolution_classification==RESOLUTION_REGISTER_SPEC_REVIEW_READY
    f=first.spec.safety_flags; assert f.spec_only is True and f.response_resolution_register_spec_only is True and f.runtime_resolution_service_allowed is False

def test_phase83_missing_or_unresolved_inputs_are_incomplete_or_review_required():
    assert _run('missing_resolution_record.json').final_resolution_classification==RESOLUTION_REGISTER_INCOMPLETE
    for name in ['incomplete_resolution_record.json','rejected_resolution_unresolved.json','deferred_blocker_without_limitation.json','superseded_resolution_missing_replacement.json','missing_non_authorization_confirmation.json','missing_owner.json','missing_follow_up_evidence_reference.json','unresolved_blocker_lacks_resolution.json','unresolved_limitation_lacks_resolution.json','stale_evidence_resolution_unresolved.json','redacted_evidence_resolution_unresolved.json','reference_only_evidence_resolution_unresolved.json','synthetic_only_evidence_resolution_unresolved.json','dependency_audit_resolution_unresolved.json','safety_review_resolution_unresolved.json','traceability_gap.json']:
        assert _run(name).final_resolution_classification in {RESOLUTION_REGISTER_REVIEW_REQUIRED,RESOLUTION_REGISTER_NOT_READY}

def test_phase83_blocked_paths_fail_closed():
    for name in ['blocked_due_xaman_payload_approval_wording.json','blocked_due_wallet_material_approval_wording.json','blocked_due_signing_submission_autofill_approval_wording.json','blocked_due_testnet_live_execution_approval_wording.json','blocked_due_runtime_resolution_service_marker.json','blocked_due_download_service_marker.json','blocked_due_api_ui_resolution_route_marker.json','blocked_due_safety_bypass_marker.json']:
        r=_run(name); assert r.final_resolution_classification==RESOLUTION_REGISTER_BLOCKED; assert r.blockers

def test_phase83_notices_traceability_and_reports_are_stable():
    r=_run('complete_spec_review_ready_resolution_register.json'); j=render_xaman_governance_response_resolution_register_json(r); m=render_xaman_governance_response_resolution_register_markdown(r)
    assert '"source_response_bundle_id": "response-82-complete"' in j
    assert '"response_resolution_register_spec_only": true' in j
    assert 'no runtime resolution service authorized' in m
    assert 'Still no runtime resolution service.' in m
    assert 'Still no API/UI resolution route.' in m
