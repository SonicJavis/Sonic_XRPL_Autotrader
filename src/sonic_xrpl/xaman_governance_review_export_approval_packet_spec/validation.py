from __future__ import annotations
from sonic_xrpl.xaman_governance_review_export_approval_packet_spec.models import *
def build_xaman_governance_review_export_approval_packet_spec(row:XamanGovernanceReviewExportApprovalPacketFixtureInput):
    errors=[]; blockers=[]; limits=[]
    def lim(i,c,s,rel,summary,block=False): limits.append(ApprovalLimitationRecord(i,c,rel,s,summary)); (blockers if block else errors).append(i)
    if not row.export_package_present: lim('missing_export_package','MISSING_EXPORT_PACKAGE','HIGH','export-package','export package missing')
    if not row.manifest_audit_present: lim('missing_manifest_audit','MISSING_MANIFEST_AUDIT','HIGH','manifest-audit','manifest audit missing')
    if row.manifest_audit_classification=='AUDIT_BLOCKED': lim('manifest_audit_blocked','MANIFEST_AUDIT_BLOCKED','CRITICAL','manifest-audit','manifest audit blocked',True)
    if row.manifest_audit_classification=='AUDIT_INCOMPLETE': lim('manifest_audit_incomplete','MANIFEST_AUDIT_INCOMPLETE','HIGH','manifest-audit','manifest audit incomplete')
    if row.manifest_audit_classification=='AUDIT_REVIEW_REQUIRED': lim('manifest_audit_review_required','MANIFEST_AUDIT_REVIEW_REQUIRED','MEDIUM','manifest-audit','manifest audit review required')
    roles={a.reviewer_role for a in row.reviewer_acknowledgements}
    for role in REQUIRED_ROLES:
        if role not in roles: lim('missing_ack_'+role.lower(),'MISSING_REVIEWER_ACKNOWLEDGEMENT','HIGH',role,'required reviewer acknowledgement missing')
    for a in row.reviewer_acknowledgements:
        if a.acknowledgement_status=='ACKNOWLEDGEMENT_REJECTED': lim('rejected_'+a.acknowledgement_id,'REJECTED_REVIEWER_ACKNOWLEDGEMENT','CRITICAL',a.acknowledgement_id,'reviewer acknowledgement rejected',True)
        elif a.acknowledgement_status in {'NOT_ACKNOWLEDGED','ACKNOWLEDGEMENT_REVIEW_REQUIRED'}: lim('review_'+a.acknowledgement_id,'MISSING_REVIEWER_ACKNOWLEDGEMENT','MEDIUM',a.acknowledgement_id,'reviewer acknowledgement requires review')
        if a.acknowledgement_limitation not in {'','none'}: lim('ack_limitation_'+a.acknowledgement_id,'ACKNOWLEDGEMENT_LIMITATION_UNRESOLVED','MEDIUM',a.acknowledgement_id,'acknowledgement limitation unresolved')
    for active,i,c,s,b in [(row.unresolved_blocker_hidden,'unresolved_blocker_hidden','UNRESOLVED_BLOCKER_HIDDEN','HIGH',False),(row.unresolved_limitation_hidden,'unresolved_limitation_hidden','UNRESOLVED_LIMITATION_HIDDEN','MEDIUM',False),(row.expired_waiver_unresolved,'expired_waiver_unresolved','EXPIRED_WAIVER_UNRESOLVED','HIGH',False),(row.revoked_waiver_unresolved,'revoked_waiver_unresolved','REVOKED_WAIVER_UNRESOLVED','HIGH',False),(row.overdue_sla_unresolved,'overdue_sla_unresolved','OVERDUE_SLA_UNRESOLVED','CRITICAL',True),(row.unsafe_waiver_attempt_unresolved,'unsafe_waiver_attempt_unresolved','UNSAFE_WAIVER_ATTEMPT_UNRESOLVED','CRITICAL',True),(row.dependency_audit_unresolved,'dependency_audit_unresolved','DEPENDENCY_AUDIT_UNRESOLVED','HIGH',False),(row.safety_review_unresolved,'safety_review_unresolved','SAFETY_REVIEW_UNRESOLVED','HIGH',False)]:
        if active: lim(i,c,s,i,i.replace('_',' '),b)
    for active,i,c in [(row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_marker','XAMAN_PAYLOAD_AMBIGUITY'),(row.invalid_wallet_material_approval_marker,'wallet_material_approval_marker','WALLET_MATERIAL_AMBIGUITY'),(row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_marker','SIGNING_SUBMISSION_AUTOFILL_AMBIGUITY'),(row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_marker','TESTNET_LIVE_APPROVAL_AMBIGUITY'),(row.invalid_runtime_approval_service_marker,'runtime_approval_service_marker','RUNTIME_APPROVAL_SERVICE_AMBIGUITY'),(row.invalid_download_service_marker,'download_service_marker','API_UI_DOWNLOAD_AMBIGUITY'),(row.invalid_api_ui_approval_route_marker,'api_ui_approval_route_marker','API_UI_DOWNLOAD_AMBIGUITY'),(row.invalid_safety_bypass_marker,'safety_bypass_marker','SAFETY_BYPASS_AMBIGUITY')]:
        if active: lim(i,c,'CRITICAL',i,c,True)
    if blockers: cls=APPROVAL_PACKET_BLOCKED
    elif (not row.export_package_present) or (not row.manifest_audit_present): cls=APPROVAL_PACKET_INCOMPLETE
    elif errors: cls=APPROVAL_PACKET_REVIEW_REQUIRED if len(errors)<4 else APPROVAL_PACKET_NOT_READY
    else: cls=APPROVAL_PACKET_SPEC_REVIEW_READY
    spec=XamanGovernanceReviewExportApprovalPacketSpec('78','Xaman governance review export approval packet contract spec',row.approval_packet_id,row.source_export_package_id,row.source_manifest_audit_id,row.deterministic_timestamp,APPROVAL_PACKET_DOMAINS,row.artifact_references,row.reviewer_acknowledgements,NON_AUTHORIZATION_NOTICES,tuple(limits))
    return XamanGovernanceReviewExportApprovalPacketReport(row.fixture_id,spec,cls,tuple(errors+blockers),tuple(blockers))
