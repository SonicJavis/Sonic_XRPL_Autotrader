from sonic_xrpl.xaman_governance_closure_review_digest_spec import build_xaman_governance_closure_review_digest_spec,load_xaman_governance_closure_review_digest_fixture
from sonic_xrpl.xaman_governance_closure_review_digest_spec.models import CLOSURE_DIGEST_BLOCKED,CLOSURE_DIGEST_INCOMPLETE,CLOSURE_DIGEST_NOT_READY,CLOSURE_DIGEST_REVIEW_REQUIRED,CLOSURE_DIGEST_SPEC_REVIEW_READY
from sonic_xrpl.xaman_governance_closure_review_digest_spec.report_writer import render_xaman_governance_closure_review_digest_json,render_xaman_governance_closure_review_digest_markdown
BASE='tests/fixtures/xaman_governance_closure_review_digest_spec'
def _run(name): return build_xaman_governance_closure_review_digest_spec(load_xaman_governance_closure_review_digest_fixture(f'{BASE}/{name}'))
def test_phase85_complete_closure_digest_is_spec_review_ready_and_deterministic():
    a=_run('complete_spec_review_ready_closure_digest.json'); b=_run('complete_spec_review_ready_closure_digest.json')
    assert a==b; assert a.final_closure_digest_classification==CLOSURE_DIGEST_SPEC_REVIEW_READY
    f=a.spec.safety_flags; assert f.spec_only and f.closure_review_digest_spec_only and (not f.runtime_closure_digest_service_allowed)
def test_phase85_missing_or_unresolved_inputs_are_incomplete_or_review_required():
    assert _run('missing_closure_evidence_bundle.json').final_closure_digest_classification==CLOSURE_DIGEST_INCOMPLETE
    for n in ['incomplete_closure_evidence_bundle.json','missing_closure_evidence_summary.json','missing_resolution_register_summary.json','missing_response_summary.json','missing_digest_snapshot_checklist_summary.json','missing_reviewer_ownership_summary.json','missing_non_authorization_summary.json','stale_closure_evidence_summary_gap.json','redacted_closure_evidence_summary_gap.json','reference_only_closure_evidence_summary_gap.json','synthetic_only_closure_evidence_summary_gap.json','hidden_unresolved_blocker.json','hidden_unresolved_limitation.json','dependency_audit_closure_summary_gap.json','safety_review_closure_summary_gap.json','traceability_gap.json']:
        assert _run(n).final_closure_digest_classification in {CLOSURE_DIGEST_REVIEW_REQUIRED,CLOSURE_DIGEST_NOT_READY}
def test_phase85_blocked_paths_fail_closed():
    for n in ['blocked_closure_evidence_bundle.json','blocked_due_xaman_payload_approval_wording.json','blocked_due_wallet_material_approval_wording.json','blocked_due_signing_submission_autofill_approval_wording.json','blocked_due_testnet_live_execution_approval_wording.json','blocked_due_runtime_closure_digest_service_marker.json','blocked_due_download_service_marker.json','blocked_due_api_ui_closure_digest_route_marker.json','blocked_due_safety_bypass_marker.json']:
        r=_run(n); assert r.final_closure_digest_classification==CLOSURE_DIGEST_BLOCKED and r.blockers
def test_phase85_notices_traceability_and_reports_are_stable():
    r=_run('complete_spec_review_ready_closure_digest.json'); j=render_xaman_governance_closure_review_digest_json(r); m=render_xaman_governance_closure_review_digest_markdown(r)
    assert '"source_closure_bundle_id": "closure-84-complete"' in j
    assert '"closure_review_digest_spec_only": true' in j
    assert 'no runtime closure digest service authorized' in m
    assert 'Still no runtime closure digest service.' in m and 'Still no API/UI closure digest route.' in m
