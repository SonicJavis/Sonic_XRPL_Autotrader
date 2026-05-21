from sonic_xrpl.xaman_governance_resolution_evidence_closure_spec import build_xaman_governance_resolution_evidence_closure_spec,load_xaman_governance_resolution_evidence_closure_fixture
from sonic_xrpl.xaman_governance_resolution_evidence_closure_spec.models import CLOSURE_BUNDLE_BLOCKED,CLOSURE_BUNDLE_INCOMPLETE,CLOSURE_BUNDLE_NOT_READY,CLOSURE_BUNDLE_REVIEW_REQUIRED,CLOSURE_BUNDLE_SPEC_REVIEW_READY
from sonic_xrpl.xaman_governance_resolution_evidence_closure_spec.report_writer import render_xaman_governance_resolution_evidence_closure_json,render_xaman_governance_resolution_evidence_closure_markdown
BASE='tests/fixtures/xaman_governance_resolution_evidence_closure_spec'
def _run(name): return build_xaman_governance_resolution_evidence_closure_spec(load_xaman_governance_resolution_evidence_closure_fixture(f'{BASE}/{name}'))
def test_phase84_complete_closure_bundle_is_spec_review_ready_and_deterministic():
    a=_run('complete_spec_review_ready_closure_bundle.json'); b=_run('complete_spec_review_ready_closure_bundle.json')
    assert a==b; assert a.final_closure_classification==CLOSURE_BUNDLE_SPEC_REVIEW_READY
    f=a.spec.safety_flags; assert f.spec_only and f.resolution_evidence_closure_spec_only and (not f.runtime_closure_service_allowed)
def test_phase84_missing_or_unresolved_inputs_are_incomplete_or_review_required():
    assert _run('missing_closure_evidence.json').final_closure_classification==CLOSURE_BUNDLE_INCOMPLETE
    for n in ['incomplete_closure_evidence.json','rejected_closure_evidence_unresolved.json','deferred_closure_without_limitation.json','superseded_closure_missing_replacement.json','missing_non_authorization_confirmation.json','missing_owner.json','missing_reviewer.json','missing_source_evidence_reference.json','unresolved_blocker_lacks_closure_evidence.json','unresolved_limitation_lacks_closure_evidence.json','stale_evidence_closure_unresolved.json','redacted_evidence_closure_unresolved.json','reference_only_evidence_closure_unresolved.json','synthetic_only_evidence_closure_unresolved.json','dependency_audit_closure_unresolved.json','safety_review_closure_unresolved.json','traceability_gap.json']:
        assert _run(n).final_closure_classification in {CLOSURE_BUNDLE_REVIEW_REQUIRED,CLOSURE_BUNDLE_NOT_READY}
def test_phase84_blocked_paths_fail_closed():
    for n in ['blocked_due_xaman_payload_approval_wording.json','blocked_due_wallet_material_approval_wording.json','blocked_due_signing_submission_autofill_approval_wording.json','blocked_due_testnet_live_execution_approval_wording.json','blocked_due_runtime_closure_service_marker.json','blocked_due_download_service_marker.json','blocked_due_api_ui_closure_route_marker.json','blocked_due_safety_bypass_marker.json']:
        r=_run(n); assert r.final_closure_classification==CLOSURE_BUNDLE_BLOCKED and r.blockers
def test_phase84_notices_traceability_and_reports_are_stable():
    r=_run('complete_spec_review_ready_closure_bundle.json'); j=render_xaman_governance_resolution_evidence_closure_json(r); m=render_xaman_governance_resolution_evidence_closure_markdown(r)
    assert '"source_resolution_register_id": "resolution-83-complete"' in j
    assert '"resolution_evidence_closure_spec_only": true' in j
    assert 'no runtime closure service authorized' in m
    assert 'Still no runtime closure service.' in m and 'Still no API/UI closure route.' in m
