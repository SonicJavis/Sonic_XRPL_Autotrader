from __future__ import annotations
from sonic_xrpl.xaman_governance_digest_review_response_spec.models import *

def build_xaman_governance_digest_review_response_spec(row:XamanGovernanceDigestReviewResponseFixtureInput):
    errors=[]; blockers=[]; findings=[]; limits=[]
    def add(i,c,s,rel,summary,block=False):
        findings.append(ResponseFindingRecord(i,c,rel,s,summary)); limits.append(ResponseLimitationRecord(i,c,rel,s,summary)); (blockers if block else errors).append(i)

    if row.missing_digest_response: add('missing_digest_response','MISSING_DIGEST_RESPONSE','HIGH','digest','missing digest response')
    if row.incomplete_digest_response: add('incomplete_digest_response','INCOMPLETE_DIGEST_RESPONSE','HIGH','digest','incomplete digest response')
    if row.rejected_digest_response: add('rejected_digest_response','REJECTED_DIGEST_RESPONSE','HIGH','digest','rejected digest response')
    if row.deferred_blocker_without_limitation: add('deferred_blocker_without_limitation','DEFERRED_BLOCKER_WITHOUT_LIMITATION','HIGH','digest','deferred blocker without limitation')
    if row.missing_non_authorization_confirmation: add('missing_non_authorization_confirmation','MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH','notices','missing non-authorization confirmation')
    if row.missing_security_reviewer_response: add('missing_security_reviewer_response','MISSING_REVIEWER_RESPONSE','HIGH','reviewer','missing security reviewer response')
    if row.missing_follow_up_evidence_reference: add('missing_follow_up_evidence_reference','MISSING_FOLLOW_UP_EVIDENCE_REFERENCE','MEDIUM','evidence','missing follow-up evidence reference')
    if row.unresolved_blocker_lacks_response: add('unresolved_blocker_lacks_response','UNRESOLVED_BLOCKER_LACKS_RESPONSE','HIGH','blocker','unresolved blocker lacks response')
    if row.unresolved_limitation_lacks_response: add('unresolved_limitation_lacks_response','UNRESOLVED_LIMITATION_LACKS_RESPONSE','MEDIUM','limitation','unresolved limitation lacks response')

    for active,i,c,s in [
        (row.stale_evidence_response_unresolved,'stale_evidence_response_unresolved','STALE_EVIDENCE_RESPONSE_UNRESOLVED','MEDIUM'),
        (row.redacted_evidence_response_unresolved,'redacted_evidence_response_unresolved','REDACTED_EVIDENCE_RESPONSE_UNRESOLVED','MEDIUM'),
        (row.reference_only_evidence_response_unresolved,'reference_only_evidence_response_unresolved','REFERENCE_ONLY_EVIDENCE_RESPONSE_UNRESOLVED','HIGH'),
        (row.synthetic_only_evidence_response_unresolved,'synthetic_only_evidence_response_unresolved','SYNTHETIC_ONLY_EVIDENCE_RESPONSE_UNRESOLVED','MEDIUM'),
        (row.dependency_audit_response_unresolved,'dependency_audit_response_unresolved','DEPENDENCY_AUDIT_RESPONSE_UNRESOLVED','HIGH'),
        (row.safety_review_response_unresolved,'safety_review_response_unresolved','SAFETY_REVIEW_RESPONSE_UNRESOLVED','HIGH'),
        (row.traceability_gap,'traceability_gap','TRACEABILITY_GAP','HIGH'),
    ]:
        if active: add(i,c,s,i,i.replace('_',' '))

    notices=set(row.non_authorization_notices)
    for notice in REQUIRED_NOTICES:
        if notice not in notices: add('missing_notice_'+notice.replace(' ','_').replace('/','_'),'MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH',notice,'missing non-authorization confirmation')

    if not any(r.reviewer_role=='SECURITY_REVIEWER' for r in row.response_records):
        add('security_reviewer_response_missing','MISSING_REVIEWER_RESPONSE','HIGH','reviewer','missing security reviewer response')

    req_domains={'DIGEST_FINDINGS','DIGEST_SECTIONS','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','NON_AUTHORIZATION_NOTICES','REVIEWER_ACKNOWLEDGEMENTS'}
    seen={r.response_domain for r in row.response_records}
    for d in sorted(req_domains-seen): add('missing_domain_'+d.lower(),'MISSING_RESPONSE_DOMAIN','HIGH',d,'missing required response domain')

    for r in row.response_records:
        if not r.non_authorization_confirmation: add('response_missing_non_auth_'+r.response_id,'MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH',r.response_id,'response missing non-authorization confirmation')
        if not r.follow_up_evidence_reference.strip(): add('response_missing_followup_'+r.response_id,'MISSING_FOLLOW_UP_EVIDENCE_REFERENCE','MEDIUM',r.response_id,'response missing follow-up evidence reference')
        if r.response_status in {'RESPONSE_BLOCKED'}: add('response_blocked_'+r.response_id,'RESPONSE_BLOCKED','CRITICAL',r.response_id,'response blocked',True)
        elif r.response_status in {'RESPONSE_REJECTED','RESPONSE_DEFERRED','RESPONSE_REVIEW_REQUIRED','RESPONSE_INCOMPLETE','RESPONSE_TRACEABILITY_GAP','RESPONSE_NON_AUTHORIZATION_MISSING'}:
            add('response_review_'+r.response_id,'RESPONSE_REVIEW_REQUIRED',r.severity or 'MEDIUM',r.response_id,'response requires review')

    for active,i,c in [
        (row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_wording','XAMAN_PAYLOAD_APPROVAL_WORDING'),
        (row.invalid_wallet_material_approval_marker,'wallet_material_approval_wording','WALLET_MATERIAL_APPROVAL_WORDING'),
        (row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_wording','SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING'),
        (row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_wording','TESTNET_LIVE_EXECUTION_APPROVAL_WORDING'),
        (row.invalid_runtime_response_service_marker,'runtime_response_service_marker','RUNTIME_RESPONSE_SERVICE_MARKER'),
        (row.invalid_download_service_marker,'download_service_marker','DOWNLOAD_SERVICE_MARKER'),
        (row.invalid_api_ui_response_route_marker,'api_ui_response_route_marker','API_UI_RESPONSE_ROUTE_MARKER'),
        (row.invalid_safety_bypass_marker,'safety_bypass_marker','SAFETY_BYPASS_MARKER')]:
        if active: add(i,c,'CRITICAL',i,c,True)

    if blockers: cls=RESPONSE_BUNDLE_BLOCKED
    elif row.missing_digest_response: cls=RESPONSE_BUNDLE_INCOMPLETE
    elif errors: cls=RESPONSE_BUNDLE_REVIEW_REQUIRED if len(errors)<4 else RESPONSE_BUNDLE_NOT_READY
    else: cls=RESPONSE_BUNDLE_SPEC_REVIEW_READY

    spec=XamanGovernanceDigestReviewResponseSpec('82','Xaman governance digest review response contract spec',row.response_bundle_id,row.source_digest_bundle_id,row.source_snapshot_id,row.deterministic_timestamp,RESPONSE_DOMAINS,row.response_records,tuple(findings),tuple(limits),REQUIRED_NOTICES)
    return XamanGovernanceDigestReviewResponseReport(row.fixture_id,spec,cls,tuple(errors+blockers),tuple(blockers))
