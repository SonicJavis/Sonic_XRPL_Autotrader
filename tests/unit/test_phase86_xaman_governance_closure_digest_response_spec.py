from sonic_xrpl.xaman_governance_closure_digest_response_spec import build_xaman_governance_closure_digest_response_spec,load_xaman_governance_closure_digest_response_fixture
from sonic_xrpl.xaman_governance_closure_digest_response_spec.models import CLOSURE_DIGEST_RESPONSE_BLOCKED,CLOSURE_DIGEST_RESPONSE_INCOMPLETE,CLOSURE_DIGEST_RESPONSE_NOT_READY,CLOSURE_DIGEST_RESPONSE_REVIEW_REQUIRED,CLOSURE_DIGEST_RESPONSE_SPEC_REVIEW_READY
from sonic_xrpl.xaman_governance_closure_digest_response_spec.report_writer import render_xaman_governance_closure_digest_response_json,render_xaman_governance_closure_digest_response_markdown
BASE='tests/fixtures/xaman_governance_closure_digest_response_spec'
def _run(name): return build_xaman_governance_closure_digest_response_spec(load_xaman_governance_closure_digest_response_fixture(f'{BASE}/{name}'))
def test_phase86_complete_closure_digest_response_bundle_is_spec_review_ready_and_deterministic():
    a=_run('complete_spec_review_ready_closure_digest_response_bundle.json'); b=_run('complete_spec_review_ready_closure_digest_response_bundle.json')
    assert a==b; assert a.final_response_classification==CLOSURE_DIGEST_RESPONSE_SPEC_REVIEW_READY
    f=a.spec.safety_flags; assert f.spec_only and f.closure_digest_response_spec_only and (not f.runtime_closure_digest_response_service_allowed)
def test_phase86_missing_or_unresolved_inputs_are_incomplete_or_review_required():
    assert _run('missing_closure_digest_response.json').final_response_classification==CLOSURE_DIGEST_RESPONSE_INCOMPLETE
    for n in ['incomplete_closure_digest_response.json','rejected_closure_digest_response_unresolved.json','deferred_blocker_without_limitation.json','superseded_response_missing_replacement.json','missing_non_authorization_confirmation.json','missing_reviewer_response.json','missing_follow_up_evidence_reference.json','missing_evidence_sufficiency_response.json','unresolved_blocker_lacks_response.json','unresolved_limitation_lacks_response.json','stale_closure_evidence_response_unresolved.json','redacted_closure_evidence_response_unresolved.json','reference_only_closure_evidence_response_unresolved.json','synthetic_only_closure_evidence_response_unresolved.json','dependency_audit_response_unresolved.json','safety_review_response_unresolved.json','traceability_gap.json']:
        assert _run(n).final_response_classification in {CLOSURE_DIGEST_RESPONSE_REVIEW_REQUIRED,CLOSURE_DIGEST_RESPONSE_NOT_READY}
def test_phase86_blocked_paths_fail_closed():
    for n in ['blocked_due_xaman_payload_approval_wording.json','blocked_due_wallet_material_approval_wording.json','blocked_due_signing_submission_autofill_approval_wording.json','blocked_due_testnet_live_execution_approval_wording.json','blocked_due_runtime_closure_digest_response_service_marker.json','blocked_due_download_service_marker.json','blocked_due_api_ui_closure_digest_response_route_marker.json','blocked_due_safety_bypass_marker.json']:
        r=_run(n); assert r.final_response_classification==CLOSURE_DIGEST_RESPONSE_BLOCKED and r.blockers
def test_phase86_notices_traceability_and_reports_are_stable():
    r=_run('complete_spec_review_ready_closure_digest_response_bundle.json'); j=render_xaman_governance_closure_digest_response_json(r); m=render_xaman_governance_closure_digest_response_markdown(r)
    assert '"source_closure_digest_bundle_id": "closure-digest-85-complete"' in j
    assert '"closure_digest_response_spec_only": true' in j
    assert 'no runtime closure digest response service authorized' in m
    assert 'Still no runtime closure digest response service.' in m and 'Still no API/UI closure digest response route.' in m
