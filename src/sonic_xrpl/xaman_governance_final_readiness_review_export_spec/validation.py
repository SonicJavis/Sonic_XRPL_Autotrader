from __future__ import annotations
from sonic_xrpl.xaman_governance_final_readiness_review_export_spec.models import *

def build_xaman_governance_final_readiness_review_export_spec(row: XamanGovernanceFinalReadinessReviewExportFixtureInput):
    errors=[]; blockers=[]; limitations=[]
    artifact_types={a.source_artifact_type for a in row.export_artifacts}
    missing_types=set(MANDATORY_ARTIFACT_TYPES)-artifact_types
    for t in sorted(missing_types):
        errors.append(f"missing_required_artifact:{t}"); limitations.append(ExportLimitationRecord(f"lim-{t.lower()}","MISSING_REQUIRED_ARTIFACT",t,"HIGH","mandatory export artifact absent"))
    presence={"phase75_final_bundle_present":row.phase75_present,"phase70_support_present":row.phase70_present,"phase71_support_present":row.phase71_present,"phase72_support_present":row.phase72_present,"phase73_support_present":row.phase73_present,"phase74_support_present":row.phase74_present}
    for check,present in presence.items():
        if not present:
            errors.append(check.replace("_present","_missing")); limitations.append(ExportLimitationRecord(f"lim-{check}","MISSING_REQUIRED_ARTIFACT",check,"HIGH","required phase artifact missing"))
    for a in row.export_artifacts:
        if a.required_classification=="REQUIRED" and not a.declared_hash:
            errors.append(f"unverifiable_artifact_hash:{a.export_artifact_id}"); limitations.append(ExportLimitationRecord(f"lim-{a.export_artifact_id}","UNVERIFIABLE_ARTIFACT_HASH",a.export_artifact_id,"MEDIUM","required artifact hash missing"))
        if a.redaction_status in {"REDACTED_SYNTHETIC_FIXTURE","REDACTED_SECURITY_DETAIL"} or a.inclusion_status=="REDACTED":
            errors.append(f"redacted_artifact_requires_review:{a.export_artifact_id}"); limitations.append(ExportLimitationRecord(f"lim-redacted-{a.export_artifact_id}","REDACTED_ARTIFACT_REQUIRES_REVIEW",a.export_artifact_id,"MEDIUM","redacted artifact requires reviewer attention"))
        if a.inclusion_status=="REFERENCE_ONLY" or a.redaction_status=="REFERENCE_ONLY_POLICY":
            errors.append(f"reference_only_artifact_requires_manual_verification:{a.export_artifact_id}"); limitations.append(ExportLimitationRecord(f"lim-reference-{a.export_artifact_id}","REFERENCE_ONLY_ARTIFACT_REQUIRES_MANUAL_VERIFICATION",a.export_artifact_id,"MEDIUM","reference-only artifact requires manual verification"))
        if a.inclusion_status in {"MISSING","BLOCKED"}:
            errors.append(f"artifact_not_exportable:{a.export_artifact_id}")
    if row.unresolved_blocker_summary:
        errors.append("unresolved_blocker_summary"); limitations.append(ExportLimitationRecord("lim-blocker-summary","UNRESOLVED_SAFETY_REVIEW","reviewer-summary","HIGH","unresolved blockers remain visible"))
    if row.unresolved_limitation_summary:
        errors.append("unresolved_limitation_summary"); limitations.append(ExportLimitationRecord("lim-limitation-summary","DOCS_DRIFT","reviewer-summary","MEDIUM","unresolved limitations remain visible"))
    for active, code, cat, sev in [
        (row.expired_waiver_included,"expired_waiver_included","EXPIRED_WAIVER","HIGH"), (row.revoked_waiver_included,"revoked_waiver_included","REVOKED_WAIVER","HIGH"),
    ]:
        if active: errors.append(code); limitations.append(ExportLimitationRecord(f"lim-{code}",cat,"phase74-waiver","HIGH",code.replace("_"," ")))
    if row.overdue_critical_sla_included:
        blockers.append("overdue_critical_sla_included"); limitations.append(ExportLimitationRecord("lim-overdue-sla","OVERDUE_CRITICAL_SLA","phase73-sla","CRITICAL","critical SLA overdue"))
    if row.unsafe_waiver_attempt_included:
        blockers.append("unsafe_waiver_attempt_included"); limitations.append(ExportLimitationRecord("lim-unsafe-waiver","UNSAFE_WAIVER_ATTEMPT","phase74-waiver","CRITICAL","unsafe waiver attempt included"))
    marker_blockers={
        row.invalid_xaman_payload_approval_marker:("xaman_payload_approval_marker","XAMAN_PAYLOAD_AMBIGUITY"), row.invalid_wallet_material_approval_marker:("wallet_material_approval_marker","WALLET_MATERIAL_AMBIGUITY"),
        row.invalid_signing_submission_autofill_approval_marker:("signing_submission_autofill_approval_marker","TESTNET_LIVE_APPROVAL_AMBIGUITY"), row.invalid_testnet_live_execution_approval_marker:("testnet_live_execution_approval_marker","TESTNET_LIVE_APPROVAL_AMBIGUITY"),
        row.invalid_runtime_export_service_marker:("runtime_export_service_marker","RUNTIME_EXPORT_SERVICE_AMBIGUITY"), row.invalid_download_service_marker:("download_service_marker","RUNTIME_EXPORT_SERVICE_AMBIGUITY"),
        row.invalid_api_ui_export_route_marker:("api_ui_export_route_marker","RUNTIME_EXPORT_SERVICE_AMBIGUITY"), row.invalid_safety_bypass_marker:("safety_bypass_marker","UNSAFE_WAIVER_ATTEMPT"),
    }
    for active,(b,cat) in marker_blockers.items():
        if active: blockers.append(b); limitations.append(ExportLimitationRecord(f"lim-{b}",cat,b,"CRITICAL","unsafe export wording or marker"))
    if blockers: readiness=EXPORT_BLOCKED
    elif missing_types or not all(presence.values()): readiness=EXPORT_INCOMPLETE
    elif errors: readiness=EXPORT_REVIEW_REQUIRED if len(errors)<4 else EXPORT_NOT_READY
    else: readiness=EXPORT_SPEC_REVIEW_READY
    summaries=(
        ReviewerSummary("EXECUTIVE_SUMMARY", f"Export package classification: {readiness}.", tuple(a.export_artifact_id for a in row.export_artifacts)),
        ReviewerSummary("INCLUDED_ARTIFACT_SUMMARY", f"Included artifact count: {sum(a.inclusion_status=='INCLUDED' for a in row.export_artifacts)}.", tuple(a.export_artifact_id for a in row.export_artifacts if a.inclusion_status=='INCLUDED')),
        ReviewerSummary("BLOCKER_SUMMARY", f"Blocker count: {len(blockers)}.", tuple()),
        ReviewerSummary("LIMITATION_SUMMARY", f"Limitation count: {len(limitations)}.", tuple(l.related_artifact_id for l in limitations)),
        ReviewerSummary("FINAL_CLASSIFICATION_SUMMARY", "Spec review packaging only; never execution readiness.", tuple()),
    )
    manifest=ExportManifest(row.manifest_id,row.export_package_id,"76",row.deterministic_timestamp,tuple(a.export_artifact_id for a in row.export_artifacts),tuple(a.declared_hash for a in row.export_artifacts),tuple(a.redaction_status for a in row.export_artifacts),tuple(s.summary_type for s in summaries),tuple(a.source_artifact_type for a in row.export_artifacts),tuple(l.limitation_id for l in limitations),tuple(blockers))
    spec=XamanGovernanceFinalReadinessReviewExportSpec("76","Xaman governance final readiness review export contract spec",row.export_package_id,row.deterministic_timestamp,EXPORT_DOMAINS,row.export_artifacts,summaries,tuple(limitations),manifest)
    return XamanGovernanceFinalReadinessReviewExportReport(row.fixture_id,spec,readiness,tuple(errors+blockers),tuple(blockers))
