from __future__ import annotations
from collections import Counter
from sonic_xrpl.xaman_governance_review_export_manifest_audit_spec.models import *

def build_xaman_governance_review_export_manifest_audit_spec(row:XamanGovernanceReviewExportManifestAuditFixtureInput):
    errors=[]; blockers=[]; findings=[]; limits=[]
    def finding(fid,cat,sev,rel,summary,blocked=False):
        findings.append(AuditFinding(fid,cat,sev,rel,summary)); limits.append(AuditLimitationRecord('lim-'+fid,cat.upper().replace(' ','_'),rel,sev,summary)); (blockers if blocked else errors).append(fid)
    if not row.manifest_present: finding('missing_export_manifest','missing required manifest','HIGH','manifest','manifest absent')
    ids=[r.source_artifact_id for r in row.manifest_audit_records]; artifact_types={r.audit_domain for r in row.manifest_audit_records if r.audit_domain in REQUIRED_ARTIFACT_TYPES}
    for req in sorted(set(REQUIRED_ARTIFACT_TYPES)-artifact_types): finding('missing_'+req.lower(),'missing required artifact','HIGH',req,'required artifact absent')
    for aid,count in Counter(ids).items():
        if aid and count>1: finding('duplicate_'+aid,'duplicate artifact ID','MEDIUM',aid,'duplicate artifact id')
    for r in row.manifest_audit_records:
        if r.audit_domain not in REQUIRED_ARTIFACT_TYPES:
            finding('undeclared_'+r.audit_record_id,'undeclared artifact','MEDIUM',r.audit_record_id,'artifact not declared in required manifest set')
        if r.audit_status=='AUDIT_HASH_MISMATCH' or r.declared_content_hash!=r.observed_content_hash: finding('hash_mismatch_'+r.audit_record_id,'hash mismatch','HIGH',r.audit_record_id,'declared and observed hashes differ')
        if r.audit_status=='AUDIT_MISSING_ARTIFACT': finding('missing_artifact_'+r.audit_record_id,'missing required artifact','HIGH',r.audit_record_id,'artifact missing')
        if r.audit_status=='AUDIT_TRACEABILITY_GAP': finding('traceability_gap_'+r.audit_record_id,'cross-phase traceability missing','HIGH',r.audit_record_id,'traceability missing')
        if not r.redaction_status: finding('redaction_missing_'+r.audit_record_id,'redaction label missing','MEDIUM',r.audit_record_id,'redaction label absent')
        if r.inclusion_status=='REFERENCE_ONLY' and r.limitation_notes in {'','none'}: finding('reference_only_without_limitation_'+r.audit_record_id,'reference-only artifact lacks limitation','MEDIUM',r.audit_record_id,'reference-only artifact lacks limitation')
        if r.redaction_status=='NO_REDACTION_REQUIRED' and r.inclusion_status=='REDACTED': finding('redaction_inconsistent_'+r.audit_record_id,'redaction label inconsistent','MEDIUM',r.audit_record_id,'redaction label inconsistent')
        if r.audit_status=='AUDIT_REDACTION_REVIEW_REQUIRED': finding('redaction_review_'+r.audit_record_id,'redaction label inconsistent','MEDIUM',r.audit_record_id,'redaction review required')
    for missing in sorted(set(REQUIRED_SUMMARY_TYPES)-set(row.reviewer_summary_types)): finding('summary_gap_'+missing.lower(),'reviewer summary missing required domain','MEDIUM',missing,'required reviewer summary missing')
    if 'unresolved_blocker' not in row.limitation_ids: finding('limitation_register_gap','limitation register omits unresolved blocker','HIGH','limitation-register','unresolved blocker omitted')
    if not row.traceability_refs: finding('cross_phase_traceability_missing','cross-phase traceability missing','HIGH','traceability-map','traceability map absent')
    for active,fid,cat in [(row.hidden_expired_waiver,'hidden_expired_waiver','expired waiver hidden'),(row.hidden_revoked_waiver,'hidden_revoked_waiver','revoked waiver hidden'),(row.hidden_overdue_critical_sla,'hidden_overdue_critical_sla','overdue critical SLA hidden'),(row.hidden_unsafe_waiver_attempt,'hidden_unsafe_waiver_attempt','unsafe waiver attempt hidden')]:
        if active: finding(fid,cat,'CRITICAL',fid,cat,True)
    for active,fid,cat in [(row.invalid_xaman_payload_approval_marker,'xaman_payload_approval_marker','Xaman payload approval wording'),(row.invalid_wallet_material_approval_marker,'wallet_material_approval_marker','wallet material approval wording'),(row.invalid_signing_submission_autofill_approval_marker,'signing_submission_autofill_approval_marker','signing/submission/autofill approval wording'),(row.invalid_testnet_live_execution_approval_marker,'testnet_live_execution_approval_marker','testnet/live execution approval wording'),(row.invalid_runtime_manifest_audit_service_marker,'runtime_manifest_audit_service_marker','runtime export audit service marker'),(row.invalid_download_service_marker,'download_service_marker','download service marker'),(row.invalid_api_ui_audit_route_marker,'api_ui_audit_route_marker','API/UI audit route marker'),(row.invalid_safety_bypass_marker,'safety_bypass_marker','safety bypass marker')]:
        if active: finding(fid,cat,'CRITICAL',fid,cat,True)
    if blockers: classification=AUDIT_BLOCKED
    elif (not row.manifest_present) or any(f.category in {'missing required artifact'} for f in findings): classification=AUDIT_INCOMPLETE
    elif errors: classification=AUDIT_REVIEW_REQUIRED if len(errors)<4 else AUDIT_NOT_READY
    else: classification=AUDIT_SPEC_REVIEW_READY
    spec=XamanGovernanceReviewExportManifestAuditSpec('77','Xaman governance review export manifest audit contract spec',row.audit_bundle_id,row.source_manifest_id,row.source_package_id,row.deterministic_timestamp,AUDIT_DOMAINS,row.manifest_audit_records,tuple(findings),tuple(limits))
    return XamanGovernanceReviewExportManifestAuditReport(row.fixture_id,spec,classification,tuple(errors+blockers),tuple(blockers))
