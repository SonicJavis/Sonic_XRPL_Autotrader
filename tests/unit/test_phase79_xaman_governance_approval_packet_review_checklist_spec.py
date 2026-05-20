from sonic_xrpl.xaman_governance_approval_packet_review_checklist_spec import build_xaman_governance_approval_packet_review_checklist_spec,load_xaman_governance_approval_packet_review_checklist_fixture
from sonic_xrpl.xaman_governance_approval_packet_review_checklist_spec.models import CHECKLIST_BLOCKED,CHECKLIST_INCOMPLETE,CHECKLIST_NOT_READY,CHECKLIST_REVIEW_REQUIRED,CHECKLIST_SPEC_REVIEW_READY
from sonic_xrpl.xaman_governance_approval_packet_review_checklist_spec.report_writer import render_xaman_governance_approval_packet_review_checklist_json,render_xaman_governance_approval_packet_review_checklist_markdown
BASE='tests/fixtures/xaman_governance_approval_packet_review_checklist_spec'
def _run(name): return build_xaman_governance_approval_packet_review_checklist_spec(load_xaman_governance_approval_packet_review_checklist_fixture(f'{BASE}/{name}'))
def test_phase79_complete_checklist_is_spec_review_ready_and_deterministic():
    first=_run('complete_spec_review_ready_checklist.json'); second=_run('complete_spec_review_ready_checklist.json'); assert first==second; assert first.final_checklist_classification==CHECKLIST_SPEC_REVIEW_READY; f=first.spec.safety_flags; assert f.spec_only is True and f.review_checklist_spec_only is True and f.runtime_checklist_service_allowed is False
def test_phase79_missing_inputs_are_incomplete_or_review_required():
    for name in ['missing_approval_packet.json','missing_manifest_audit.json','missing_export_package.json','missing_final_readiness_bundle.json']:
        assert _run(name).final_checklist_classification==CHECKLIST_INCOMPLETE
    for name in ['incomplete_approval_packet.json','missing_security_acknowledgement.json','missing_non_authorization_notice.json','ambiguous_non_authorization_wording.json','hidden_unresolved_blocker.json','hidden_unresolved_limitation.json','expired_waiver_unresolved.json','revoked_waiver_unresolved.json','dependency_audit_unresolved.json','safety_review_unresolved.json','traceability_gap.json']:
        assert _run(name).final_checklist_classification in {CHECKLIST_REVIEW_REQUIRED,CHECKLIST_NOT_READY}
def test_phase79_blocked_paths_fail_closed():
    for name in ['rejected_reviewer_acknowledgement.json','blocked_manifest_audit.json','overdue_sla_unresolved.json','unsafe_waiver_attempt_unresolved.json','blocked_due_xaman_payload_approval_wording.json','blocked_due_wallet_material_approval_wording.json','blocked_due_signing_submission_autofill_approval_wording.json','blocked_due_testnet_live_execution_approval_wording.json','blocked_due_runtime_checklist_service_marker.json','blocked_due_download_service_marker.json','blocked_due_api_ui_checklist_route_marker.json','blocked_due_safety_bypass_marker.json']:
        r=_run(name); assert r.final_checklist_classification==CHECKLIST_BLOCKED; assert r.blockers
def test_phase79_notices_traceability_and_reports_are_stable():
    r=_run('complete_spec_review_ready_checklist.json'); j=render_xaman_governance_approval_packet_review_checklist_json(r); m=render_xaman_governance_approval_packet_review_checklist_markdown(r); assert '"source_approval_packet_id": "packet-78-complete"' in j; assert '"review_checklist_spec_only": true' in j; assert 'no runtime checklist service authorized' in m; assert 'Still no runtime checklist service.' in m; assert 'Still no API/UI checklist route.' in m
