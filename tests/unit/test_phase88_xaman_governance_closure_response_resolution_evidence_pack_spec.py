from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec import build_xaman_governance_closure_response_resolution_evidence_pack_spec,load_xaman_governance_closure_response_resolution_evidence_pack_fixture
from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec.models import EVIDENCE_PACK_BLOCKED,EVIDENCE_PACK_INCOMPLETE,EVIDENCE_PACK_NOT_READY,EVIDENCE_PACK_REVIEW_REQUIRED,EVIDENCE_PACK_SPEC_REVIEW_READY
from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec.report_writer import render_xaman_governance_closure_response_resolution_evidence_pack_json,render_xaman_governance_closure_response_resolution_evidence_pack_markdown

BASE='tests/fixtures/xaman_governance_closure_response_resolution_evidence_pack_spec'
def _run(name): return build_xaman_governance_closure_response_resolution_evidence_pack_spec(load_xaman_governance_closure_response_resolution_evidence_pack_fixture(f'{BASE}/{name}'))

def test_phase88_complete_evidence_pack_is_spec_review_ready_and_deterministic():
    a=_run('complete_spec_review_ready_evidence_pack.json'); b=_run('complete_spec_review_ready_evidence_pack.json')
    assert a==b; assert a.final_evidence_pack_classification==EVIDENCE_PACK_SPEC_REVIEW_READY
    flags=a.spec.safety_flags
    assert flags.spec_only and flags.closure_response_resolution_evidence_pack_spec_only and not flags.runtime_closure_response_resolution_evidence_pack_service_allowed

def test_phase88_missing_or_unresolved_inputs_are_incomplete_or_review_required():
    assert _run('missing_evidence_pack.json').final_evidence_pack_classification==EVIDENCE_PACK_INCOMPLETE
    for name in ['incomplete_evidence_pack.json','missing_required_evidence.json','stale_evidence_unresolved.json','redacted_evidence_unresolved.json','reference_only_evidence_unresolved.json','synthetic_only_evidence_unresolved.json','unverified_evidence_unresolved.json','missing_non_authorization_confirmation.json','missing_owner.json','missing_reviewer.json','missing_follow_up_evidence_reference.json','missing_evidence_sufficiency_mapping.json','unresolved_blocker_lacks_evidence.json','unresolved_limitation_lacks_evidence.json','dependency_audit_evidence_unresolved.json','safety_review_evidence_unresolved.json','superseded_evidence_missing_replacement.json','rejected_evidence_unresolved.json','traceability_gap.json']:
        assert _run(name).final_evidence_pack_classification in {EVIDENCE_PACK_REVIEW_REQUIRED,EVIDENCE_PACK_NOT_READY}

def test_phase88_blocked_paths_fail_closed():
    for name in ['blocked_due_xaman_payload_approval_wording.json','blocked_due_wallet_material_approval_wording.json','blocked_due_signing_submission_autofill_approval_wording.json','blocked_due_testnet_live_execution_approval_wording.json','blocked_due_runtime_closure_response_resolution_evidence_pack_service_marker.json','blocked_due_download_service_marker.json','blocked_due_api_ui_evidence_pack_route_marker.json','blocked_due_safety_bypass_marker.json']:
        report=_run(name)
        assert report.final_evidence_pack_classification==EVIDENCE_PACK_BLOCKED and report.blockers

def test_phase88_reports_include_notices_traceability_and_stable_flags():
    report=_run('complete_spec_review_ready_evidence_pack.json')
    json_report=render_xaman_governance_closure_response_resolution_evidence_pack_json(report)
    markdown_report=render_xaman_governance_closure_response_resolution_evidence_pack_markdown(report)
    assert '"source_closure_response_resolution_register_id": "closure-response-resolution-register-87-complete"' in json_report
    assert '"closure_response_resolution_evidence_pack_spec_only": true' in json_report
    assert 'no runtime closure response resolution evidence pack service authorized' in markdown_report
    assert 'Still no runtime closure response resolution evidence pack service.' in markdown_report and 'Still no API/UI evidence-pack route.' in markdown_report
