from sonic_xrpl.xaman_governance_digest_review_response_spec import build_xaman_governance_digest_review_response_spec,load_xaman_governance_digest_review_response_fixture
from sonic_xrpl.xaman_governance_digest_review_response_spec.models import RESPONSE_BUNDLE_BLOCKED,RESPONSE_BUNDLE_INCOMPLETE,RESPONSE_BUNDLE_NOT_READY,RESPONSE_BUNDLE_REVIEW_REQUIRED,RESPONSE_BUNDLE_SPEC_REVIEW_READY
from sonic_xrpl.xaman_governance_digest_review_response_spec.report_writer import render_xaman_governance_digest_review_response_json,render_xaman_governance_digest_review_response_markdown
BASE='tests/fixtures/xaman_governance_digest_review_response_spec'
def _run(name): return build_xaman_governance_digest_review_response_spec(load_xaman_governance_digest_review_response_fixture(f'{BASE}/{name}'))

def test_phase82_complete_response_bundle_is_spec_review_ready_and_deterministic():
    first=_run('complete_spec_review_ready_response_bundle.json'); second=_run('complete_spec_review_ready_response_bundle.json')
    assert first==second; assert first.final_response_classification==RESPONSE_BUNDLE_SPEC_REVIEW_READY
    f=first.spec.safety_flags; assert f.spec_only is True and f.digest_review_response_spec_only is True and f.runtime_response_service_allowed is False

def test_phase82_missing_or_unresolved_inputs_are_incomplete_or_review_required():
    assert _run('missing_digest_response.json').final_response_classification==RESPONSE_BUNDLE_INCOMPLETE
    for name in ['incomplete_digest_response.json','rejected_digest_response.json','deferred_blocker_without_limitation.json','missing_non_authorization_confirmation.json','missing_security_reviewer_response.json','missing_follow_up_evidence_reference.json','unresolved_blocker_lacks_response.json','unresolved_limitation_lacks_response.json','stale_evidence_response_unresolved.json','redacted_evidence_response_unresolved.json','reference_only_evidence_response_unresolved.json','synthetic_only_evidence_response_unresolved.json','dependency_audit_response_unresolved.json','safety_review_response_unresolved.json','traceability_gap.json']:
        assert _run(name).final_response_classification in {RESPONSE_BUNDLE_REVIEW_REQUIRED,RESPONSE_BUNDLE_NOT_READY}

def test_phase82_blocked_paths_fail_closed():
    for name in ['blocked_due_xaman_payload_approval_wording.json','blocked_due_wallet_material_approval_wording.json','blocked_due_signing_submission_autofill_approval_wording.json','blocked_due_testnet_live_execution_approval_wording.json','blocked_due_runtime_response_service_marker.json','blocked_due_download_service_marker.json','blocked_due_api_ui_response_route_marker.json','blocked_due_safety_bypass_marker.json']:
        r=_run(name); assert r.final_response_classification==RESPONSE_BUNDLE_BLOCKED; assert r.blockers

def test_phase82_notices_traceability_and_reports_are_stable():
    r=_run('complete_spec_review_ready_response_bundle.json'); j=render_xaman_governance_digest_review_response_json(r); m=render_xaman_governance_digest_review_response_markdown(r)
    assert '"source_digest_bundle_id": "digest-81-complete"' in j
    assert '"digest_review_response_spec_only": true' in j
    assert 'no runtime response service authorized' in m
    assert 'Still no runtime response service.' in m
    assert 'Still no API/UI response route.' in m
