from __future__ import annotations
from sonic_xrpl.xaman_governance_snapshot_review_digest_spec.models import *
def build_xaman_governance_snapshot_review_digest_spec(row:XamanGovernanceSnapshotReviewDigestFixtureInput):
    errors=[]; blockers=[]; findings=[]; limits=[]
    def add(i,c,s,rel,summary,block=False):
        findings.append(DigestFindingRecord(i,c,rel,s,summary)); limits.append(DigestLimitationRecord(i,c,rel,s,summary)); (blockers if block else errors).append(i)
    if not row.snapshot_present: add('snapshot_missing','SNAPSHOT_MISSING','HIGH','snapshot','snapshot missing')
    elif row.snapshot_classification=='SNAPSHOT_BLOCKED': add('snapshot_blocked','SNAPSHOT_BLOCKED','CRITICAL','snapshot','snapshot blocked',True)
    elif row.snapshot_classification!='SNAPSHOT_SPEC_REVIEW_READY': add('snapshot_incomplete','SNAPSHOT_INCOMPLETE','HIGH','snapshot','snapshot incomplete')
    if not row.checklist_present: add('checklist_summary_missing','MISSING_CHECKLIST_SUMMARY','HIGH','checklist','missing checklist summary')
    if row.checklist_present and row.checklist_classification!='CHECKLIST_SPEC_REVIEW_READY': add('checklist_not_spec_ready','CHECKLIST_NOT_SPEC_READY','HIGH','checklist','checklist not spec ready')
    if not row.reviewer_ack_summary_present: add('reviewer_ack_summary_missing','MISSING_REVIEWER_ACK_SUMMARY','HIGH','ack-summary','missing reviewer acknowledgement summary')
    notices=set(row.non_authorization_notices)
    for notice in REQUIRED_NOTICES:
        if notice not in notices: add('missing_notice_'+notice.replace(' ','_').replace('/','_'),'MISSING_NON_AUTHORIZATION_SUMMARY','HIGH',notice,'missing non-authorization summary')
    req_domains={'EVIDENCE_SNAPSHOT','APPROVAL_CHECKLIST','APPROVAL_PACKET','MANIFEST_AUDIT','EXPORT_PACKAGE','FINAL_READINESS_BUNDLE','NON_AUTHORIZATION_NOTICES','REVIEWER_ACKNOWLEDGEMENTS'}
    seen={s.digest_domain for s in row.digest_sections}
    for d in sorted(req_domains-seen): add('missing_domain_'+d.lower(),'MISSING_DIGEST_SECTION', 'HIGH', d, 'required digest section missing')
    for s in row.digest_sections:
        if s.digest_status in {'DIGEST_BLOCKED','DIGEST_FAILED'}: add('section_'+s.digest_section_id,'DIGEST_SECTION_FAILED',s.severity or 'HIGH',s.digest_section_id,'digest section failed',s.digest_status=='DIGEST_BLOCKED')
        elif s.digest_status in {'DIGEST_REVIEW_REQUIRED','DIGEST_INCOMPLETE','DIGEST_TRACEABILITY_GAP','DIGEST_NON_AUTHORIZATION_MISSING'}: add('section_'+s.digest_section_id,'DIGEST_SECTION_REVIEW_REQUIRED',s.severity or 'MEDIUM',s.digest_section_id,'digest section requires review')
    for active,i,c,s,b in [(row.stale_evidence_summary_gap,'stale_evidence_summary_gap','STALE_EVIDENCE_HIDDEN','MEDIUM',False),(row.redacted_evidence_summary_gap,'redacted_evidence_summary_gap','REDACTED_EVIDENCE_HIDDEN','MEDIUM',False),(row.reference_only_evidence_summary_gap,'reference_only_evidence_summary_gap','REFERENCE_ONLY_EVIDENCE_HIDDEN','HIGH',False),(row.synthetic_only_evidence_summary_gap,'synthetic_only_evidence_summary_gap','SYNTHETIC_ONLY_EVIDENCE_HIDDEN','MEDIUM',False),(row.hidden_unresolved_blocker,'hidden_unresolved_blocker','UNRESOLVED_BLOCKER_SUMMARY_MISSING','HIGH',False),(row.hidden_unresolved_limitation,'hidden_unresolved_limitation','UNRESOLVED_LIMITATION_SUMMARY_MISSING','MEDIUM',False),(row.dependency_audit_summary_gap,'dependency_audit_summary_gap','DEPENDENCY_AUDIT_SUMMARY_GAP','HIGH',False),(row.safety_review_summary_gap,'safety_review_summary_gap','SAFETY_REVIEW_SUMMARY_GAP','HIGH',False),(row.traceability_gap,'traceability_gap','TRACEABILITY_SUMMARY_GAP','HIGH',False)]:
        if active: add(i,c,s,i,i.replace('_',' '),b)
    for active,i,c in [(row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_wording','XAMAN_PAYLOAD_APPROVAL_WORDING'),(row.invalid_wallet_material_approval_marker,'wallet_material_approval_wording','WALLET_MATERIAL_APPROVAL_WORDING'),(row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_wording','SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING'),(row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_wording','TESTNET_LIVE_EXECUTION_APPROVAL_WORDING'),(row.invalid_runtime_digest_service_marker,'runtime_digest_service_marker','RUNTIME_DIGEST_SERVICE_MARKER'),(row.invalid_download_service_marker,'download_service_marker','DOWNLOAD_SERVICE_MARKER'),(row.invalid_api_ui_digest_route_marker,'api_ui_digest_route_marker','API_UI_DIGEST_ROUTE_MARKER'),(row.invalid_safety_bypass_marker,'safety_bypass_marker','SAFETY_BYPASS_MARKER')]:
        if active: add(i,c,'CRITICAL',i,c,True)
    if blockers: cls=DIGEST_BLOCKED
    elif not row.snapshot_present: cls=DIGEST_INCOMPLETE
    elif errors: cls=DIGEST_REVIEW_REQUIRED if len(errors)<4 else DIGEST_NOT_READY
    else: cls=DIGEST_SPEC_REVIEW_READY
    spec=XamanGovernanceSnapshotReviewDigestSpec('81','Xaman governance snapshot review digest contract spec',row.digest_bundle_id,row.source_snapshot_id,row.source_checklist_id,row.deterministic_timestamp,DIGEST_DOMAINS,row.digest_sections,tuple(findings),tuple(limits),REQUIRED_NOTICES)
    return XamanGovernanceSnapshotReviewDigestReport(row.fixture_id,spec,cls,tuple(errors+blockers),tuple(blockers))
