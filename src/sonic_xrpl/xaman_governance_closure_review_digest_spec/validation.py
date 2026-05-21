from __future__ import annotations
from sonic_xrpl.xaman_governance_closure_review_digest_spec.models import *
def build_xaman_governance_closure_review_digest_spec(row:XamanGovernanceClosureReviewDigestFixtureInput):
    errors=[]; blockers=[]; findings=[]; limits=[]
    def add(i,c,s,rel,summary,block=False):
        findings.append(ClosureDigestFindingRecord(i,c,rel,s,summary)); limits.append(ClosureDigestLimitationRecord(i,c,rel,s,summary)); (blockers if block else errors).append(i)
    if not row.closure_bundle_present: add('closure_bundle_missing','CLOSURE_BUNDLE_MISSING','HIGH','closure-bundle','closure bundle missing')
    elif row.closure_bundle_classification=='CLOSURE_BUNDLE_BLOCKED': add('closure_bundle_blocked','CLOSURE_BUNDLE_BLOCKED','CRITICAL','closure-bundle','closure bundle blocked',True)
    elif row.closure_bundle_classification!='CLOSURE_BUNDLE_SPEC_REVIEW_READY': add('closure_bundle_incomplete','CLOSURE_BUNDLE_INCOMPLETE','HIGH','closure-bundle','closure bundle incomplete')
    if row.resolution_register_classification!='RESOLUTION_REGISTER_SPEC_REVIEW_READY': add('resolution_register_not_spec_ready','RESOLUTION_REGISTER_NOT_SPEC_READY','HIGH','resolution-register','resolution register not spec ready')
    if row.missing_closure_evidence_summary: add('missing_closure_evidence_summary','MISSING_CLOSURE_EVIDENCE_SUMMARY','HIGH','closure-evidence','missing closure evidence summary')
    if row.missing_resolution_register_summary: add('missing_resolution_register_summary','MISSING_RESOLUTION_REGISTER_SUMMARY','HIGH','resolution-register','missing resolution register summary')
    if row.missing_response_summary: add('missing_response_summary','MISSING_RESPONSE_SUMMARY','HIGH','response','missing response summary')
    if row.missing_digest_snapshot_checklist_summary: add('missing_digest_snapshot_checklist_summary','MISSING_DIGEST_SNAPSHOT_CHECKLIST_SUMMARY','HIGH','summary','missing digest/snapshot/checklist summary')
    if not row.reviewer_ownership_summary_present: add('missing_reviewer_ownership_summary','MISSING_REVIEWER_OWNERSHIP_SUMMARY','HIGH','ownership','missing reviewer ownership summary')
    if row.missing_non_authorization_summary: add('missing_non_authorization_summary','MISSING_NON_AUTHORIZATION_SUMMARY','HIGH','notices','missing non-authorization summary')
    notices=set(row.non_authorization_notices)
    for n in REQUIRED_NOTICES:
        if n not in notices: add('missing_notice_'+n.replace(' ','_').replace('/','_'),'MISSING_NON_AUTHORIZATION_SUMMARY','HIGH',n,'missing non-authorization summary')
    req={'RESOLUTION_EVIDENCE_CLOSURE','CLOSURE_EVIDENCE','EVIDENCE_SUFFICIENCY','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','NON_AUTHORIZATION_CONFIRMATIONS','REVIEWER_OWNERSHIP'}
    seen={s.digest_domain for s in row.closure_digest_sections}
    for d in sorted(req-seen): add('missing_domain_'+d.lower(),'MISSING_CLOSURE_DIGEST_SECTION','HIGH',d,'required closure digest section missing')
    for s in row.closure_digest_sections:
        if s.digest_status in {'CLOSURE_DIGEST_BLOCKED','CLOSURE_DIGEST_FAILED'}: add('section_'+s.closure_digest_section_id,'CLOSURE_DIGEST_SECTION_FAILED',s.severity or 'HIGH',s.closure_digest_section_id,'closure digest section failed',s.digest_status=='CLOSURE_DIGEST_BLOCKED')
        elif s.digest_status in {'CLOSURE_DIGEST_REVIEW_REQUIRED','CLOSURE_DIGEST_INCOMPLETE','CLOSURE_DIGEST_TRACEABILITY_GAP','CLOSURE_DIGEST_NON_AUTHORIZATION_MISSING'}: add('section_'+s.closure_digest_section_id,'CLOSURE_DIGEST_SECTION_REVIEW_REQUIRED',s.severity or 'MEDIUM',s.closure_digest_section_id,'closure digest section requires review')
        if s.insufficient_evidence_count>0: add('section_insufficient_'+s.closure_digest_section_id,'CLOSURE_EVIDENCE_SUFFICIENCY_GAP','MEDIUM',s.closure_digest_section_id,'closure evidence sufficiency gap')
    for active,i,c,s in [(row.stale_closure_evidence_summary_gap,'stale_closure_evidence_summary_gap','STALE_CLOSURE_EVIDENCE_HIDDEN','MEDIUM'),(row.redacted_closure_evidence_summary_gap,'redacted_closure_evidence_summary_gap','REDACTED_CLOSURE_EVIDENCE_HIDDEN','MEDIUM'),(row.reference_only_closure_evidence_summary_gap,'reference_only_closure_evidence_summary_gap','REFERENCE_ONLY_CLOSURE_EVIDENCE_HIDDEN','HIGH'),(row.synthetic_only_closure_evidence_summary_gap,'synthetic_only_closure_evidence_summary_gap','SYNTHETIC_ONLY_CLOSURE_EVIDENCE_HIDDEN','MEDIUM'),(row.hidden_unresolved_blocker,'hidden_unresolved_blocker','UNRESOLVED_BLOCKER_SUMMARY_MISSING','HIGH'),(row.hidden_unresolved_limitation,'hidden_unresolved_limitation','UNRESOLVED_LIMITATION_SUMMARY_MISSING','MEDIUM'),(row.dependency_audit_closure_summary_gap,'dependency_audit_closure_summary_gap','DEPENDENCY_AUDIT_CLOSURE_SUMMARY_GAP','HIGH'),(row.safety_review_closure_summary_gap,'safety_review_closure_summary_gap','SAFETY_REVIEW_CLOSURE_SUMMARY_GAP','HIGH'),(row.traceability_gap,'traceability_gap','TRACEABILITY_SUMMARY_GAP','HIGH')]:
        if active: add(i,c,s,i,i.replace('_',' '))
    for active,i,c in [(row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_wording','XAMAN_PAYLOAD_APPROVAL_WORDING'),(row.invalid_wallet_material_approval_marker,'wallet_material_approval_wording','WALLET_MATERIAL_APPROVAL_WORDING'),(row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_wording','SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING'),(row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_wording','TESTNET_LIVE_EXECUTION_APPROVAL_WORDING'),(row.invalid_runtime_closure_digest_service_marker,'runtime_closure_digest_service_marker','RUNTIME_CLOSURE_DIGEST_SERVICE_MARKER'),(row.invalid_download_service_marker,'download_service_marker','DOWNLOAD_SERVICE_MARKER'),(row.invalid_api_ui_closure_digest_route_marker,'api_ui_closure_digest_route_marker','API_UI_CLOSURE_DIGEST_ROUTE_MARKER'),(row.invalid_safety_bypass_marker,'safety_bypass_marker','SAFETY_BYPASS_MARKER')]:
        if active: add(i,c,'CRITICAL',i,c,True)
    if blockers: cls=CLOSURE_DIGEST_BLOCKED
    elif not row.closure_bundle_present: cls=CLOSURE_DIGEST_INCOMPLETE
    elif errors: cls=CLOSURE_DIGEST_REVIEW_REQUIRED if len(errors)<4 else CLOSURE_DIGEST_NOT_READY
    else: cls=CLOSURE_DIGEST_SPEC_REVIEW_READY
    spec=XamanGovernanceClosureReviewDigestSpec('85','Xaman governance closure review digest contract spec',row.closure_digest_bundle_id,row.source_closure_bundle_id,row.source_resolution_register_id,row.deterministic_timestamp,CLOSURE_DIGEST_DOMAINS,row.closure_digest_sections,tuple(findings),tuple(limits),REQUIRED_NOTICES)
    return XamanGovernanceClosureReviewDigestReport(row.fixture_id,spec,cls,tuple(errors+blockers),tuple(blockers))
