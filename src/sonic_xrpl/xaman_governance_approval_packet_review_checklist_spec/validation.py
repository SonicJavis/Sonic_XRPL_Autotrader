from __future__ import annotations
from sonic_xrpl.xaman_governance_approval_packet_review_checklist_spec.models import *
def build_xaman_governance_approval_packet_review_checklist_spec(row:XamanGovernanceApprovalPacketReviewChecklistFixtureInput):
    errors=[]; blockers=[]; findings=[]; limits=[]
    def add(i,c,s,rel,summary,block=False):
        findings.append(ChecklistFindingRecord(i,c,rel,s,summary)); limits.append(ChecklistLimitationRecord(i,c,rel,s,summary)); (blockers if block else errors).append(i)
    if not row.approval_packet_present: add('approval_packet_missing','APPROVAL_PACKET_MISSING','HIGH','approval-packet','approval packet missing')
    elif row.approval_packet_classification not in {'APPROVAL_PACKET_SPEC_REVIEW_READY'}: add('approval_packet_incomplete','APPROVAL_PACKET_INCOMPLETE','HIGH','approval-packet','approval packet incomplete')
    if not row.manifest_audit_present: add('manifest_audit_missing','MANIFEST_AUDIT_MISSING','HIGH','manifest-audit','manifest audit missing')
    elif row.manifest_audit_classification=='AUDIT_BLOCKED': add('manifest_audit_blocked','MANIFEST_AUDIT_BLOCKED','CRITICAL','manifest-audit','manifest audit blocked',True)
    if not row.export_package_present: add('export_package_missing','EXPORT_PACKAGE_MISSING','HIGH','export-package','export package missing')
    if not row.final_readiness_bundle_present: add('final_readiness_bundle_missing','FINAL_READINESS_BUNDLE_MISSING','HIGH','final-readiness-bundle','final readiness bundle missing')
    roles=set(row.reviewer_roles)
    for role in REQUIRED_ROLES:
        if role not in roles: add('missing_ack_'+role.lower(),'MISSING_REVIEWER_ACKNOWLEDGEMENT','HIGH',role,'required reviewer acknowledgement missing')
    notices=set(row.non_authorization_notices)
    for notice in REQUIRED_NOTICES:
        if notice not in notices: add('missing_notice_'+notice.replace(' ','_').replace('/','_'),'MISSING_NON_AUTHORIZATION_NOTICE','HIGH',notice,'required non-authorization notice missing')
    if row.ambiguous_non_authorization_wording: add('ambiguous_non_authorization_wording','NON_AUTHORIZATION_WORDING_AMBIGUITY','HIGH','notices','non-authorization wording ambiguous')
    for item in row.checklist_items:
        if item.checklist_status in {'CHECK_BLOCKED','CHECK_FAILED'}: add('item_'+item.checklist_item_id,'CHECKLIST_ITEM_FAILED',item.finding_severity or 'HIGH',item.checklist_item_id,'checklist item failed',item.checklist_status=='CHECK_BLOCKED')
        elif item.checklist_status in {'CHECK_REVIEW_REQUIRED','CHECK_INCOMPLETE','CHECK_NON_AUTHORIZATION_MISSING','CHECK_TRACEABILITY_GAP'}: add('item_'+item.checklist_item_id,'CHECKLIST_ITEM_REVIEW_REQUIRED',item.finding_severity or 'MEDIUM',item.checklist_item_id,'checklist item requires review')
    for active,i,c,s,b in [(row.hidden_unresolved_blocker,'hidden_unresolved_blocker','UNRESOLVED_BLOCKER','HIGH',False),(row.hidden_unresolved_limitation,'hidden_unresolved_limitation','UNRESOLVED_LIMITATION','MEDIUM',False),(row.expired_waiver_unresolved,'expired_waiver_unresolved','EXPIRED_WAIVER','HIGH',False),(row.revoked_waiver_unresolved,'revoked_waiver_unresolved','REVOKED_WAIVER','HIGH',False),(row.overdue_sla_unresolved,'overdue_sla_unresolved','OVERDUE_SLA','CRITICAL',True),(row.dependency_audit_unresolved,'dependency_audit_unresolved','DEPENDENCY_AUDIT_UNRESOLVED','HIGH',False),(row.safety_review_unresolved,'safety_review_unresolved','SAFETY_REVIEW_UNRESOLVED','HIGH',False),(row.traceability_gap,'traceability_gap','TRACEABILITY_GAP','HIGH',False),(row.unsafe_waiver_attempt_unresolved,'unsafe_waiver_attempt_unresolved','UNSAFE_WAIVER_ATTEMPT','CRITICAL',True)]:
        if active: add(i,c,s,i,i.replace('_',' '),b)
    for active,i,c in [(row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_wording','XAMAN_PAYLOAD_APPROVAL_WORDING'),(row.invalid_wallet_material_approval_marker,'wallet_material_approval_wording','WALLET_MATERIAL_APPROVAL_WORDING'),(row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_wording','SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING'),(row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_wording','TESTNET_LIVE_EXECUTION_APPROVAL_WORDING'),(row.invalid_runtime_checklist_service_marker,'runtime_checklist_service_marker','RUNTIME_CHECKLIST_SERVICE_MARKER'),(row.invalid_download_service_marker,'download_service_marker','DOWNLOAD_SERVICE_MARKER'),(row.invalid_api_ui_checklist_route_marker,'api_ui_checklist_route_marker','API_UI_CHECKLIST_ROUTE_MARKER'),(row.invalid_safety_bypass_marker,'safety_bypass_marker','SAFETY_BYPASS_MARKER')]:
        if active: add(i,c,'CRITICAL',i,c,True)
    if blockers: cls=CHECKLIST_BLOCKED
    elif not row.approval_packet_present or not row.manifest_audit_present or not row.export_package_present or not row.final_readiness_bundle_present: cls=CHECKLIST_INCOMPLETE
    elif errors: cls=CHECKLIST_REVIEW_REQUIRED if len(errors)<4 else CHECKLIST_NOT_READY
    else: cls=CHECKLIST_SPEC_REVIEW_READY
    spec=XamanGovernanceApprovalPacketReviewChecklistSpec('79','Xaman governance approval packet review checklist contract spec',row.checklist_bundle_id,row.source_approval_packet_id,row.deterministic_timestamp,CHECKLIST_DOMAINS,row.checklist_items,tuple(findings),tuple(limits),REQUIRED_NOTICES)
    return XamanGovernanceApprovalPacketReviewChecklistReport(row.fixture_id,spec,cls,tuple(errors+blockers),tuple(blockers))
