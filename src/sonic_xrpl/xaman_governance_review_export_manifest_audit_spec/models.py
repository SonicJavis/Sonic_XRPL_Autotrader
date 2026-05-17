from __future__ import annotations
from dataclasses import dataclass
from typing import Any

AUDIT_NOT_READY="AUDIT_NOT_READY"; AUDIT_REVIEW_REQUIRED="AUDIT_REVIEW_REQUIRED"; AUDIT_SPEC_REVIEW_READY="AUDIT_SPEC_REVIEW_READY"; AUDIT_BLOCKED="AUDIT_BLOCKED"; AUDIT_INCOMPLETE="AUDIT_INCOMPLETE"
AUDIT_DOMAINS=("EXPORT_MANIFEST","EXPORT_ARTIFACTS","REDACTION_LABELS","REVIEWER_SUMMARIES","LIMITATION_REGISTER","TRACEABILITY_MAP","FINAL_READINESS_BUNDLE","SIGNOFF_MATRIX","EVIDENCE_ATTESTATION","REVIEW_WORKFLOW","ESCALATION_SLA","EXCEPTION_WAIVER_REGISTER","SAFETY_GUARDS","DEPENDENCY_AUDIT","RUNTIME_PROFILE","POLICY_DOCS")
AUDIT_STATUSES=("AUDIT_NOT_STARTED","AUDIT_REVIEW_REQUIRED","AUDIT_PASS_FOR_SPEC_REVIEW","AUDIT_BLOCKED","AUDIT_INCOMPLETE","AUDIT_HASH_MISMATCH","AUDIT_MISSING_ARTIFACT","AUDIT_REDACTION_REVIEW_REQUIRED","AUDIT_TRACEABILITY_GAP")
REQUIRED_SUMMARY_TYPES=("EXECUTIVE_SUMMARY","INCLUDED_ARTIFACT_SUMMARY","BLOCKER_SUMMARY","LIMITATION_SUMMARY","FINAL_CLASSIFICATION_SUMMARY")
REQUIRED_ARTIFACT_TYPES=("PHASE75_FINAL_READINESS_BUNDLE_REPORT","PHASE70_SIGNOFF_MATRIX_REPORT","PHASE71_ATTESTATION_BUNDLE_REPORT","PHASE72_REVIEW_WORKFLOW_REPORT","PHASE73_SLA_BUNDLE_REPORT","PHASE74_WAIVER_REGISTER_REPORT","DEPENDENCY_AUDIT_SUMMARY","SAFETY_SCAN_SUMMARY")

@dataclass(frozen=True)
class Phase77SafetyFlags:
    spec_only: bool=True; manifest_audit_spec_only: bool=True; runtime_manifest_audit_service_allowed: bool=False; download_service_allowed: bool=False; api_route_allowed: bool=False; dashboard_ui_allowed: bool=False; safety_bypass_allowed: bool=False; testnet_execution_allowed: bool=False; xaman_payload_creation_allowed: bool=False; xaman_api_calls_allowed: bool=False; xaman_sdk_dependency_allowed: bool=False; signing_allowed: bool=False; submission_allowed: bool=False; autofill_allowed: bool=False; wallet_material_allowed: bool=False; live_execution_allowed: bool=False; runtime_mutation_allowed: bool=False

@dataclass(frozen=True)
class ManifestAuditRecord:
    audit_record_id:str; audit_domain:str; source_manifest_id:str; source_artifact_id:str; source_phase_number:str; declared_source_reference:str; declared_content_hash:str; observed_content_hash:str; inclusion_status:str; redaction_status:str; reviewer_visibility:str; audit_status:str; finding_severity:str; limitation_notes:str; safety_flags:tuple[str,...]

@dataclass(frozen=True)
class AuditFinding:
    finding_id:str; category:str; severity:str; related_record_id:str; summary:str

@dataclass(frozen=True)
class AuditLimitationRecord:
    limitation_id:str; category:str; related_record_id:str; severity:str; summary:str

@dataclass(frozen=True)
class XamanGovernanceReviewExportManifestAuditSpec:
    phase:str; objective:str; audit_bundle_id:str; source_manifest_id:str; source_package_id:str; deterministic_timestamp:str; audit_domains:tuple[str,...]; manifest_audit_records:tuple[ManifestAuditRecord,...]; audit_findings:tuple[AuditFinding,...]; audit_limitation_register:tuple[AuditLimitationRecord,...]; safety_flags:Phase77SafetyFlags=Phase77SafetyFlags()

@dataclass(frozen=True)
class XamanGovernanceReviewExportManifestAuditFixtureInput:
    fixture_id:str; audit_bundle_id:str; source_manifest_id:str; source_package_id:str; deterministic_timestamp:str; manifest_present:bool; manifest_audit_records:tuple[ManifestAuditRecord,...]; reviewer_summary_types:tuple[str,...]; limitation_ids:tuple[str,...]; traceability_refs:tuple[str,...]; hidden_expired_waiver:bool; hidden_revoked_waiver:bool; hidden_overdue_critical_sla:bool; hidden_unsafe_waiver_attempt:bool; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_manifest_audit_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_audit_route_marker:bool=False; invalid_safety_bypass_marker:bool=False

@dataclass(frozen=True)
class XamanGovernanceReviewExportManifestAuditReport:
    fixture_id:str; spec:XamanGovernanceReviewExportManifestAuditSpec; final_audit_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]

def jsonable(value:Any)->Any:
    if hasattr(value,'__dataclass_fields__'): return {k:jsonable(getattr(value,k)) for k in value.__dataclass_fields__}
    if isinstance(value,tuple): return [jsonable(v) for v in value]
    if isinstance(value,list): return [jsonable(v) for v in value]
    if isinstance(value,dict): return {str(k):jsonable(v) for k,v in value.items()}
    return value
