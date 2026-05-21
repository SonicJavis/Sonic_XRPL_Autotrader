from __future__ import annotations
from sonic_xrpl.xaman_governance_closure_digest_response_spec.models import *
def build_xaman_governance_closure_digest_response_spec(row:XamanGovernanceClosureDigestResponseFixtureInput):
    errors=[]; blockers=[]; findings=[]; limits=[]
    def add(i,c,s,rel,summary,block=False):
        findings.append(ClosureDigestResponseFindingRecord(i,c,rel,s,summary)); limits.append(ClosureDigestResponseLimitationRecord(i,c,rel,s,summary)); (blockers if block else errors).append(i)
    if row.missing_closure_digest_response: add('missing_closure_digest_response','MISSING_CLOSURE_DIGEST_RESPONSE','HIGH','response','missing closure digest response')
    if row.incomplete_closure_digest_response: add('incomplete_closure_digest_response','INCOMPLETE_CLOSURE_DIGEST_RESPONSE','HIGH','response','incomplete closure digest response')
    if row.rejected_closure_digest_response_unresolved: add('rejected_closure_digest_response_unresolved','REJECTED_CLOSURE_DIGEST_RESPONSE_UNRESOLVED','HIGH','response','rejected closure digest response unresolved')
    if row.deferred_blocker_without_limitation: add('deferred_blocker_without_limitation','DEFERRED_BLOCKER_WITHOUT_LIMITATION','HIGH','response','deferred blocker without limitation')
    if row.superseded_response_missing_replacement: add('superseded_response_missing_replacement','SUPERSEDED_RESPONSE_MISSING_REPLACEMENT','HIGH','response','superseded response missing replacement')
    if row.missing_non_authorization_confirmation: add('missing_non_authorization_confirmation','MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH','notices','missing non-authorization confirmation')
    if row.missing_reviewer_response: add('missing_reviewer_response','MISSING_REVIEWER_RESPONSE','HIGH','reviewer','missing reviewer response')
    if row.missing_follow_up_evidence_reference: add('missing_follow_up_evidence_reference','MISSING_FOLLOW_UP_EVIDENCE_REFERENCE','MEDIUM','evidence','missing follow-up evidence reference')
    if row.missing_evidence_sufficiency_response: add('missing_evidence_sufficiency_response','MISSING_EVIDENCE_SUFFICIENCY_RESPONSE','HIGH','sufficiency','missing evidence sufficiency response')
    if row.unresolved_blocker_lacks_response: add('unresolved_blocker_lacks_response','UNRESOLVED_BLOCKER_LACKS_RESPONSE','HIGH','blocker','unresolved blocker lacks response')
    if row.unresolved_limitation_lacks_response: add('unresolved_limitation_lacks_response','UNRESOLVED_LIMITATION_LACKS_RESPONSE','MEDIUM','limitation','unresolved limitation lacks response')
    for active,i,c,s in [(row.stale_closure_evidence_response_unresolved,'stale_closure_evidence_response_unresolved','STALE_CLOSURE_EVIDENCE_RESPONSE_UNRESOLVED','MEDIUM'),(row.redacted_closure_evidence_response_unresolved,'redacted_closure_evidence_response_unresolved','REDACTED_CLOSURE_EVIDENCE_RESPONSE_UNRESOLVED','MEDIUM'),(row.reference_only_closure_evidence_response_unresolved,'reference_only_closure_evidence_response_unresolved','REFERENCE_ONLY_CLOSURE_EVIDENCE_RESPONSE_UNRESOLVED','HIGH'),(row.synthetic_only_closure_evidence_response_unresolved,'synthetic_only_closure_evidence_response_unresolved','SYNTHETIC_ONLY_CLOSURE_EVIDENCE_RESPONSE_UNRESOLVED','MEDIUM'),(row.dependency_audit_response_unresolved,'dependency_audit_response_unresolved','DEPENDENCY_AUDIT_RESPONSE_UNRESOLVED','HIGH'),(row.safety_review_response_unresolved,'safety_review_response_unresolved','SAFETY_REVIEW_RESPONSE_UNRESOLVED','HIGH'),(row.traceability_gap,'traceability_gap','TRACEABILITY_GAP','HIGH')]:
        if active: add(i,c,s,i,i.replace('_',' '))
    notices=set(row.non_authorization_notices)
    for n in REQUIRED_NOTICES:
        if n not in notices: add('missing_notice_'+n.replace(' ','_').replace('/','_'),'MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH',n,'missing non-authorization confirmation')
    req={'CLOSURE_REVIEW_DIGEST','CLOSURE_DIGEST_FINDINGS','CLOSURE_DIGEST_SECTIONS','EVIDENCE_SUFFICIENCY','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','NON_AUTHORIZATION_CONFIRMATIONS','REVIEWER_OWNERSHIP'}
    seen={r.response_domain for r in row.response_records}
    for d in sorted(req-seen): add('missing_domain_'+d.lower(),'MISSING_RESPONSE_DOMAIN','HIGH',d,'missing required response domain')
    for r in row.response_records:
        if not r.reviewer_role.strip(): add('record_missing_reviewer_'+r.closure_digest_response_id,'MISSING_REVIEWER_RESPONSE','HIGH',r.closure_digest_response_id,'missing reviewer response')
        if not r.non_authorization_confirmation: add('record_missing_non_auth_'+r.closure_digest_response_id,'MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH',r.closure_digest_response_id,'missing non-authorization confirmation')
        if not r.required_follow_up_evidence_references: add('record_missing_follow_up_'+r.closure_digest_response_id,'MISSING_FOLLOW_UP_EVIDENCE_REFERENCE','MEDIUM',r.closure_digest_response_id,'missing follow-up evidence reference')
        if not r.evidence_sufficiency_response.strip(): add('record_missing_sufficiency_'+r.closure_digest_response_id,'MISSING_EVIDENCE_SUFFICIENCY_RESPONSE','HIGH',r.closure_digest_response_id,'missing evidence sufficiency response')
        if r.response_status=='CLOSURE_DIGEST_RESPONSE_SUPERSEDED' and not r.superseded_by_response_id.strip(): add('record_superseded_missing_replacement_'+r.closure_digest_response_id,'SUPERSEDED_RESPONSE_MISSING_REPLACEMENT','HIGH',r.closure_digest_response_id,'superseded response missing replacement')
        if r.response_status=='CLOSURE_DIGEST_RESPONSE_DEFERRED' and not r.unresolved_limitation_references: add('record_deferred_without_limitation_'+r.closure_digest_response_id,'DEFERRED_BLOCKER_WITHOUT_LIMITATION','HIGH',r.closure_digest_response_id,'deferred blocker without limitation')
        if r.response_status=='CLOSURE_DIGEST_RESPONSE_BLOCKED': add('record_blocked_'+r.closure_digest_response_id,'CLOSURE_DIGEST_RESPONSE_BLOCKED','CRITICAL',r.closure_digest_response_id,'closure digest response blocked',True)
        elif r.response_status in {'CLOSURE_DIGEST_RESPONSE_REJECTED','CLOSURE_DIGEST_RESPONSE_DEFERRED','CLOSURE_DIGEST_RESPONSE_REVIEW_REQUIRED','CLOSURE_DIGEST_RESPONSE_INCOMPLETE','CLOSURE_DIGEST_RESPONSE_TRACEABILITY_GAP','CLOSURE_DIGEST_RESPONSE_NON_AUTHORIZATION_MISSING'}:
            add('record_review_'+r.closure_digest_response_id,'CLOSURE_DIGEST_RESPONSE_REVIEW_REQUIRED',r.severity or 'MEDIUM',r.closure_digest_response_id,'closure digest response requires review')
        if r.evidence_sufficiency_response in {'SUFFICIENCY_BLOCKED'}: add('record_sufficiency_blocked_'+r.closure_digest_response_id,'SUFFICIENCY_BLOCKED','CRITICAL',r.closure_digest_response_id,'sufficiency blocked',True)
        elif r.evidence_sufficiency_response in {'SUFFICIENCY_REVIEW_REQUIRED','SUFFICIENCY_REJECTED','SUFFICIENCY_INCOMPLETE','SUFFICIENCY_NEEDS_MORE_EVIDENCE','SUFFICIENCY_SUPERSEDED'}:
            add('record_sufficiency_review_'+r.closure_digest_response_id,'SUFFICIENCY_REVIEW_REQUIRED',r.severity or 'MEDIUM',r.closure_digest_response_id,'sufficiency requires review')
    for active,i,c in [(row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_wording','XAMAN_PAYLOAD_APPROVAL_WORDING'),(row.invalid_wallet_material_approval_marker,'wallet_material_approval_wording','WALLET_MATERIAL_APPROVAL_WORDING'),(row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_wording','SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING'),(row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_wording','TESTNET_LIVE_EXECUTION_APPROVAL_WORDING'),(row.invalid_runtime_closure_digest_response_service_marker,'runtime_closure_digest_response_service_marker','RUNTIME_CLOSURE_DIGEST_RESPONSE_SERVICE_MARKER'),(row.invalid_download_service_marker,'download_service_marker','DOWNLOAD_SERVICE_MARKER'),(row.invalid_api_ui_closure_digest_response_route_marker,'api_ui_closure_digest_response_route_marker','API_UI_CLOSURE_DIGEST_RESPONSE_ROUTE_MARKER'),(row.invalid_safety_bypass_marker,'safety_bypass_marker','SAFETY_BYPASS_MARKER')]:
        if active: add(i,c,'CRITICAL',i,c,True)
    if blockers: cls=CLOSURE_DIGEST_RESPONSE_BLOCKED
    elif row.missing_closure_digest_response: cls=CLOSURE_DIGEST_RESPONSE_INCOMPLETE
    elif errors: cls=CLOSURE_DIGEST_RESPONSE_REVIEW_REQUIRED if len(errors)<4 else CLOSURE_DIGEST_RESPONSE_NOT_READY
    else: cls=CLOSURE_DIGEST_RESPONSE_SPEC_REVIEW_READY
    spec=XamanGovernanceClosureDigestResponseSpec('86','Xaman governance closure digest response contract spec',row.closure_digest_response_bundle_id,row.source_closure_digest_bundle_id,row.source_closure_bundle_id,row.deterministic_timestamp,RESPONSE_DOMAINS,row.response_records,tuple(findings),tuple(limits),REQUIRED_NOTICES)
    return XamanGovernanceClosureDigestResponseReport(row.fixture_id,spec,cls,tuple(errors+blockers),tuple(blockers))
