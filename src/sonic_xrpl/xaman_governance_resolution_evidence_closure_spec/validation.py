from __future__ import annotations
from sonic_xrpl.xaman_governance_resolution_evidence_closure_spec.models import *

def build_xaman_governance_resolution_evidence_closure_spec(row:XamanGovernanceResolutionEvidenceClosureFixtureInput):
    errors=[]; blockers=[]; findings=[]; limits=[]
    def add(i,c,s,rel,summary,block=False):
        findings.append(ClosureFindingRecord(i,c,rel,s,summary)); limits.append(ClosureLimitationRecord(i,c,rel,s,summary)); (blockers if block else errors).append(i)
    if row.missing_closure_evidence: add('missing_closure_evidence','MISSING_CLOSURE_EVIDENCE','HIGH','closure','missing closure evidence')
    if row.incomplete_closure_evidence: add('incomplete_closure_evidence','INCOMPLETE_CLOSURE_EVIDENCE','HIGH','closure','incomplete closure evidence')
    if row.rejected_closure_evidence_unresolved: add('rejected_closure_evidence_unresolved','REJECTED_CLOSURE_EVIDENCE_UNRESOLVED','HIGH','closure','rejected closure evidence unresolved')
    if row.deferred_closure_without_limitation: add('deferred_closure_without_limitation','DEFERRED_CLOSURE_WITHOUT_LIMITATION','HIGH','closure','deferred closure without limitation')
    if row.superseded_closure_missing_replacement: add('superseded_closure_missing_replacement','SUPERSEDED_CLOSURE_MISSING_REPLACEMENT','HIGH','closure','superseded closure missing replacement')
    if row.missing_non_authorization_confirmation: add('missing_non_authorization_confirmation','MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH','notices','missing non-authorization confirmation')
    if row.missing_owner: add('missing_owner','MISSING_OWNER','HIGH','owner','missing owner')
    if row.missing_reviewer: add('missing_reviewer','MISSING_REVIEWER','HIGH','reviewer','missing reviewer')
    if row.missing_source_evidence_reference: add('missing_source_evidence_reference','MISSING_SOURCE_EVIDENCE_REFERENCE','MEDIUM','evidence','missing source evidence reference')
    if row.unresolved_blocker_lacks_closure_evidence: add('unresolved_blocker_lacks_closure_evidence','UNRESOLVED_BLOCKER_LACKS_CLOSURE_EVIDENCE','HIGH','blocker','unresolved blocker lacks closure evidence')
    if row.unresolved_limitation_lacks_closure_evidence: add('unresolved_limitation_lacks_closure_evidence','UNRESOLVED_LIMITATION_LACKS_CLOSURE_EVIDENCE','MEDIUM','limitation','unresolved limitation lacks closure evidence')
    for active,i,c,s in [(row.stale_evidence_closure_unresolved,'stale_evidence_closure_unresolved','STALE_EVIDENCE_CLOSURE_UNRESOLVED','MEDIUM'),(row.redacted_evidence_closure_unresolved,'redacted_evidence_closure_unresolved','REDACTED_EVIDENCE_CLOSURE_UNRESOLVED','MEDIUM'),(row.reference_only_evidence_closure_unresolved,'reference_only_evidence_closure_unresolved','REFERENCE_ONLY_EVIDENCE_CLOSURE_UNRESOLVED','HIGH'),(row.synthetic_only_evidence_closure_unresolved,'synthetic_only_evidence_closure_unresolved','SYNTHETIC_ONLY_EVIDENCE_CLOSURE_UNRESOLVED','MEDIUM'),(row.dependency_audit_closure_unresolved,'dependency_audit_closure_unresolved','DEPENDENCY_AUDIT_CLOSURE_UNRESOLVED','HIGH'),(row.safety_review_closure_unresolved,'safety_review_closure_unresolved','SAFETY_REVIEW_CLOSURE_UNRESOLVED','HIGH'),(row.traceability_gap,'traceability_gap','TRACEABILITY_GAP','HIGH')]:
        if active: add(i,c,s,i,i.replace('_',' '))
    notices=set(row.non_authorization_notices)
    for n in REQUIRED_NOTICES:
        if n not in notices: add('missing_notice_'+n.replace(' ','_').replace('/','_'),'MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH',n,'missing non-authorization confirmation')
    req={'RESPONSE_RESOLUTION_REGISTER','CLOSURE_EVIDENCE','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','FOLLOW_UP_EVIDENCE','NON_AUTHORIZATION_CONFIRMATIONS','REVIEWER_OWNERSHIP'}
    seen={r.closure_domain for r in row.closure_evidence_records}
    for d in sorted(req-seen): add('missing_domain_'+d.lower(),'MISSING_CLOSURE_DOMAIN','HIGH',d,'missing required closure domain')
    for r in row.closure_evidence_records:
        if not r.owner_role.strip(): add('record_missing_owner_'+r.closure_evidence_id,'MISSING_OWNER','HIGH',r.closure_evidence_id,'missing owner')
        if not r.reviewer_role.strip(): add('record_missing_reviewer_'+r.closure_evidence_id,'MISSING_REVIEWER','HIGH',r.closure_evidence_id,'missing reviewer')
        if not r.non_authorization_confirmation: add('record_missing_non_auth_'+r.closure_evidence_id,'MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH',r.closure_evidence_id,'missing non-authorization confirmation')
        if not r.source_evidence_references: add('record_missing_source_evidence_'+r.closure_evidence_id,'MISSING_SOURCE_EVIDENCE_REFERENCE','MEDIUM',r.closure_evidence_id,'missing source evidence reference')
        if r.evidence_status=='CLOSURE_EVIDENCE_SUPERSEDED' and not r.superseded_by_closure_evidence_id.strip(): add('record_superseded_missing_replacement_'+r.closure_evidence_id,'SUPERSEDED_CLOSURE_MISSING_REPLACEMENT','HIGH',r.closure_evidence_id,'superseded closure missing replacement')
        if r.evidence_status=='CLOSURE_EVIDENCE_DEFERRED' and not r.unresolved_limitation_references: add('record_deferred_without_limitation_'+r.closure_evidence_id,'DEFERRED_CLOSURE_WITHOUT_LIMITATION','HIGH',r.closure_evidence_id,'deferred closure without limitation')
        if r.evidence_status=='CLOSURE_EVIDENCE_BLOCKED': add('record_blocked_'+r.closure_evidence_id,'CLOSURE_EVIDENCE_BLOCKED','CRITICAL',r.closure_evidence_id,'closure evidence blocked',True)
        elif r.evidence_status in {'CLOSURE_EVIDENCE_REJECTED','CLOSURE_EVIDENCE_DEFERRED','CLOSURE_EVIDENCE_REVIEW_REQUIRED','CLOSURE_EVIDENCE_INCOMPLETE','CLOSURE_EVIDENCE_TRACEABILITY_GAP','CLOSURE_EVIDENCE_NON_AUTHORIZATION_MISSING'}:
            add('record_review_'+r.closure_evidence_id,'CLOSURE_EVIDENCE_REVIEW_REQUIRED',r.severity or 'MEDIUM',r.closure_evidence_id,'closure evidence requires review')
        if r.evidence_sufficiency_status in {'BLOCKED'}: add('record_sufficiency_blocked_'+r.closure_evidence_id,'CLOSURE_EVIDENCE_BLOCKED','CRITICAL',r.closure_evidence_id,'closure evidence sufficiency blocked',True)
        elif r.evidence_sufficiency_status in {'INSUFFICIENT_EVIDENCE','REVIEW_REQUIRED','INCOMPLETE','SUPERSEDED','REJECTED'}:
            add('record_sufficiency_review_'+r.closure_evidence_id,'CLOSURE_EVIDENCE_REVIEW_REQUIRED',r.severity or 'MEDIUM',r.closure_evidence_id,'closure evidence sufficiency requires review')
    for active,i,c in [(row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_wording','XAMAN_PAYLOAD_APPROVAL_WORDING'),(row.invalid_wallet_material_approval_marker,'wallet_material_approval_wording','WALLET_MATERIAL_APPROVAL_WORDING'),(row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_wording','SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING'),(row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_wording','TESTNET_LIVE_EXECUTION_APPROVAL_WORDING'),(row.invalid_runtime_closure_service_marker,'runtime_closure_service_marker','RUNTIME_CLOSURE_SERVICE_MARKER'),(row.invalid_download_service_marker,'download_service_marker','DOWNLOAD_SERVICE_MARKER'),(row.invalid_api_ui_closure_route_marker,'api_ui_closure_route_marker','API_UI_CLOSURE_ROUTE_MARKER'),(row.invalid_safety_bypass_marker,'safety_bypass_marker','SAFETY_BYPASS_MARKER')]:
        if active: add(i,c,'CRITICAL',i,c,True)
    if blockers: cls=CLOSURE_BUNDLE_BLOCKED
    elif row.missing_closure_evidence: cls=CLOSURE_BUNDLE_INCOMPLETE
    elif errors: cls=CLOSURE_BUNDLE_REVIEW_REQUIRED if len(errors)<4 else CLOSURE_BUNDLE_NOT_READY
    else: cls=CLOSURE_BUNDLE_SPEC_REVIEW_READY
    spec=XamanGovernanceResolutionEvidenceClosureSpec('84','Xaman governance resolution evidence closure contract spec',row.closure_bundle_id,row.source_resolution_register_id,row.source_response_bundle_id,row.deterministic_timestamp,CLOSURE_DOMAINS,row.closure_evidence_records,tuple(findings),tuple(limits),REQUIRED_NOTICES)
    return XamanGovernanceResolutionEvidenceClosureReport(row.fixture_id,spec,cls,tuple(errors+blockers),tuple(blockers))
