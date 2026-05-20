from sonic_xrpl.xaman_governance_snapshot_review_digest_spec import build_xaman_governance_snapshot_review_digest_spec,load_xaman_governance_snapshot_review_digest_fixture
from sonic_xrpl.xaman_governance_snapshot_review_digest_spec.models import DIGEST_BLOCKED,DIGEST_INCOMPLETE,DIGEST_NOT_READY,DIGEST_REVIEW_REQUIRED,DIGEST_SPEC_REVIEW_READY
from sonic_xrpl.xaman_governance_snapshot_review_digest_spec.report_writer import render_xaman_governance_snapshot_review_digest_json,render_xaman_governance_snapshot_review_digest_markdown
BASE='tests/fixtures/xaman_governance_snapshot_review_digest_spec'
def _run(name): return build_xaman_governance_snapshot_review_digest_spec(load_xaman_governance_snapshot_review_digest_fixture(f'{BASE}/{name}'))
def test_phase81_complete_digest_is_spec_review_ready_and_deterministic():
    first=_run('complete_spec_review_ready_digest.json'); second=_run('complete_spec_review_ready_digest.json'); assert first==second; assert first.final_digest_classification==DIGEST_SPEC_REVIEW_READY; f=first.spec.safety_flags; assert f.spec_only is True and f.snapshot_review_digest_spec_only is True and f.runtime_digest_service_allowed is False
def test_phase81_missing_inputs_are_incomplete_or_review_required():
    assert _run('missing_evidence_snapshot.json').final_digest_classification==DIGEST_INCOMPLETE
    for name in ['incomplete_evidence_snapshot.json','missing_checklist_summary.json','missing_approval_packet_summary.json','missing_manifest_audit_summary.json','missing_export_package_summary.json','missing_final_readiness_summary.json','missing_reviewer_ack_summary.json','missing_non_authorization_summary.json','stale_evidence_summary_gap.json','redacted_evidence_summary_gap.json','reference_only_evidence_summary_gap.json','synthetic_only_evidence_summary_gap.json','hidden_unresolved_blocker.json','hidden_unresolved_limitation.json','dependency_audit_summary_gap.json','safety_review_summary_gap.json','traceability_gap.json']:
        assert _run(name).final_digest_classification in {DIGEST_REVIEW_REQUIRED,DIGEST_NOT_READY}
def test_phase81_blocked_paths_fail_closed():
    for name in ['blocked_evidence_snapshot.json','blocked_due_xaman_payload_approval_wording.json','blocked_due_wallet_material_approval_wording.json','blocked_due_signing_submission_autofill_approval_wording.json','blocked_due_testnet_live_execution_approval_wording.json','blocked_due_runtime_digest_service_marker.json','blocked_due_download_service_marker.json','blocked_due_api_ui_digest_route_marker.json','blocked_due_safety_bypass_marker.json']:
        r=_run(name); assert r.final_digest_classification==DIGEST_BLOCKED; assert r.blockers
def test_phase81_notices_traceability_and_reports_are_stable():
    r=_run('complete_spec_review_ready_digest.json'); j=render_xaman_governance_snapshot_review_digest_json(r); m=render_xaman_governance_snapshot_review_digest_markdown(r); assert '"source_snapshot_id": "snapshot-80-complete"' in j; assert '"snapshot_review_digest_spec_only": true' in j; assert 'no runtime digest service authorized' in m; assert 'Still no runtime digest service.' in m; assert 'Still no API/UI digest route.' in m
