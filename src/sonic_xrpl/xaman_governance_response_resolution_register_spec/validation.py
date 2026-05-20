from __future__ import annotations
from sonic_xrpl.xaman_governance_response_resolution_register_spec.models import *

def build_xaman_governance_response_resolution_register_spec(row:XamanGovernanceResponseResolutionRegisterFixtureInput):
    errors=[]; blockers=[]; findings=[]; limits=[]
    def add(i,c,s,rel,summary,block=False):
        findings.append(ResolutionFindingRecord(i,c,rel,s,summary)); limits.append(ResolutionLimitationRecord(i,c,rel,s,summary)); (blockers if block else errors).append(i)

    if row.missing_resolution_record: add('missing_resolution_record','MISSING_RESOLUTION_RECORD','HIGH','resolution','missing resolution record')
    if row.incomplete_resolution_record: add('incomplete_resolution_record','INCOMPLETE_RESOLUTION_RECORD','HIGH','resolution','incomplete resolution record')
    if row.rejected_resolution_unresolved: add('rejected_resolution_unresolved','REJECTED_RESOLUTION_UNRESOLVED','HIGH','resolution','rejected resolution unresolved')
    if row.deferred_blocker_without_limitation: add('deferred_blocker_without_limitation','DEFERRED_BLOCKER_WITHOUT_LIMITATION','HIGH','resolution','deferred blocker without limitation')
    if row.superseded_resolution_missing_replacement: add('superseded_resolution_missing_replacement','SUPERSEDED_RESOLUTION_MISSING_REPLACEMENT','HIGH','resolution','superseded resolution missing replacement')
    if row.missing_non_authorization_confirmation: add('missing_non_authorization_confirmation','MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH','notices','missing non-authorization confirmation')
    if row.missing_owner: add('missing_owner','MISSING_OWNER','HIGH','owner','missing owner')
    if row.missing_follow_up_evidence_reference: add('missing_follow_up_evidence_reference','MISSING_FOLLOW_UP_EVIDENCE_REFERENCE','MEDIUM','evidence','missing follow-up evidence reference')
    if row.unresolved_blocker_lacks_resolution: add('unresolved_blocker_lacks_resolution','UNRESOLVED_BLOCKER_LACKS_RESOLUTION','HIGH','blocker','unresolved blocker lacks resolution')
    if row.unresolved_limitation_lacks_resolution: add('unresolved_limitation_lacks_resolution','UNRESOLVED_LIMITATION_LACKS_RESOLUTION','MEDIUM','limitation','unresolved limitation lacks resolution')

    for active,i,c,s in [
        (row.stale_evidence_resolution_unresolved,'stale_evidence_resolution_unresolved','STALE_EVIDENCE_RESOLUTION_UNRESOLVED','MEDIUM'),
        (row.redacted_evidence_resolution_unresolved,'redacted_evidence_resolution_unresolved','REDACTED_EVIDENCE_RESOLUTION_UNRESOLVED','MEDIUM'),
        (row.reference_only_evidence_resolution_unresolved,'reference_only_evidence_resolution_unresolved','REFERENCE_ONLY_EVIDENCE_RESOLUTION_UNRESOLVED','HIGH'),
        (row.synthetic_only_evidence_resolution_unresolved,'synthetic_only_evidence_resolution_unresolved','SYNTHETIC_ONLY_EVIDENCE_RESOLUTION_UNRESOLVED','MEDIUM'),
        (row.dependency_audit_resolution_unresolved,'dependency_audit_resolution_unresolved','DEPENDENCY_AUDIT_RESOLUTION_UNRESOLVED','HIGH'),
        (row.safety_review_resolution_unresolved,'safety_review_resolution_unresolved','SAFETY_REVIEW_RESOLUTION_UNRESOLVED','HIGH'),
        (row.traceability_gap,'traceability_gap','TRACEABILITY_GAP','HIGH')]:
        if active: add(i,c,s,i,i.replace('_',' '))

    notices=set(row.non_authorization_notices)
    for notice in REQUIRED_NOTICES:
        if notice not in notices: add('missing_notice_'+notice.replace(' ','_').replace('/','_'),'MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH',notice,'missing non-authorization confirmation')

    req_domains={'DIGEST_REVIEW_RESPONSES','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','FOLLOW_UP_EVIDENCE','NON_AUTHORIZATION_CONFIRMATIONS','REVIEWER_OWNERSHIP'}
    seen={r.resolution_domain for r in row.resolution_records}
    for d in sorted(req_domains-seen): add('missing_domain_'+d.lower(),'MISSING_RESOLUTION_DOMAIN','HIGH',d,'missing required resolution domain')

    for r in row.resolution_records:
        if not r.owner_role.strip(): add('record_missing_owner_'+r.resolution_id,'MISSING_OWNER','HIGH',r.resolution_id,'missing owner')
        if not r.non_authorization_confirmation: add('record_missing_non_auth_'+r.resolution_id,'MISSING_NON_AUTHORIZATION_CONFIRMATION','HIGH',r.resolution_id,'missing non-authorization confirmation')
        if not r.follow_up_evidence_references: add('record_missing_followup_'+r.resolution_id,'MISSING_FOLLOW_UP_EVIDENCE_REFERENCE','MEDIUM',r.resolution_id,'missing follow-up evidence reference')
        if r.resolution_category=='RESOLUTION_SUPERSEDED' and not r.superseded_by_resolution_id.strip(): add('record_superseded_missing_replacement_'+r.resolution_id,'SUPERSEDED_RESOLUTION_MISSING_REPLACEMENT','HIGH',r.resolution_id,'superseded resolution missing replacement')
        if r.resolution_category=='RESOLUTION_DEFERRED' and not r.unresolved_limitation_references: add('record_deferred_without_limitation_'+r.resolution_id,'DEFERRED_BLOCKER_WITHOUT_LIMITATION','HIGH',r.resolution_id,'deferred blocker without limitation')
        if r.resolution_status in {'RESOLUTION_BLOCKED'}: add('record_blocked_'+r.resolution_id,'RESOLUTION_BLOCKED','CRITICAL',r.resolution_id,'resolution blocked',True)
        elif r.resolution_status in {'RESOLUTION_REJECTED','RESOLUTION_DEFERRED','RESOLUTION_REVIEW_REQUIRED','RESOLUTION_INCOMPLETE','RESOLUTION_TRACEABILITY_GAP','RESOLUTION_NON_AUTHORIZATION_MISSING'}:
            add('record_review_'+r.resolution_id,'RESOLUTION_REVIEW_REQUIRED',r.severity or 'MEDIUM',r.resolution_id,'resolution requires review')

    for active,i,c in [
        (row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_wording','XAMAN_PAYLOAD_APPROVAL_WORDING'),
        (row.invalid_wallet_material_approval_marker,'wallet_material_approval_wording','WALLET_MATERIAL_APPROVAL_WORDING'),
        (row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_wording','SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING'),
        (row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_wording','TESTNET_LIVE_EXECUTION_APPROVAL_WORDING'),
        (row.invalid_runtime_resolution_service_marker,'runtime_resolution_service_marker','RUNTIME_RESOLUTION_SERVICE_MARKER'),
        (row.invalid_download_service_marker,'download_service_marker','DOWNLOAD_SERVICE_MARKER'),
        (row.invalid_api_ui_resolution_route_marker,'api_ui_resolution_route_marker','API_UI_RESOLUTION_ROUTE_MARKER'),
        (row.invalid_safety_bypass_marker,'safety_bypass_marker','SAFETY_BYPASS_MARKER')]:
        if active: add(i,c,'CRITICAL',i,c,True)

    if blockers: cls=RESOLUTION_REGISTER_BLOCKED
    elif row.missing_resolution_record: cls=RESOLUTION_REGISTER_INCOMPLETE
    elif errors: cls=RESOLUTION_REGISTER_REVIEW_REQUIRED if len(errors)<4 else RESOLUTION_REGISTER_NOT_READY
    else: cls=RESOLUTION_REGISTER_SPEC_REVIEW_READY

    spec=XamanGovernanceResponseResolutionRegisterSpec('83','Xaman governance response resolution register contract spec',row.resolution_register_id,row.source_response_bundle_id,row.source_digest_bundle_id,row.deterministic_timestamp,RESOLUTION_DOMAINS,row.resolution_records,tuple(findings),tuple(limits),REQUIRED_NOTICES)
    return XamanGovernanceResponseResolutionRegisterReport(row.fixture_id,spec,cls,tuple(errors+blockers),tuple(blockers))
