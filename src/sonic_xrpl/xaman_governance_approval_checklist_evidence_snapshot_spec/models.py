from __future__ import annotations
from dataclasses import dataclass
from typing import Any
SNAPSHOT_NOT_READY='SNAPSHOT_NOT_READY'; SNAPSHOT_REVIEW_REQUIRED='SNAPSHOT_REVIEW_REQUIRED'; SNAPSHOT_SPEC_REVIEW_READY='SNAPSHOT_SPEC_REVIEW_READY'; SNAPSHOT_BLOCKED='SNAPSHOT_BLOCKED'; SNAPSHOT_INCOMPLETE='SNAPSHOT_INCOMPLETE'
SNAPSHOT_DOMAINS=('APPROVAL_CHECKLIST','APPROVAL_PACKET','MANIFEST_AUDIT','EXPORT_PACKAGE','FINAL_READINESS_BUNDLE','SIGNOFF_MATRIX','EVIDENCE_ATTESTATION','REVIEW_WORKFLOW','ESCALATION_SLA','EXCEPTION_WAIVER_REGISTER','NON_AUTHORIZATION_NOTICES','REVIEWER_ACKNOWLEDGEMENTS','LIMITATION_REGISTER','SAFETY_GUARDS','DEPENDENCY_AUDIT','POLICY_DOCS','TRACEABILITY_MAP')
REQUIRED_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime snapshot service authorized','no download/API/UI route authorized','no safety bypass authorized')
@dataclass(frozen=True)
class Phase80SafetyFlags:
    spec_only:bool=True; evidence_snapshot_spec_only:bool=True; runtime_snapshot_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class SnapshotEvidenceRecord:
    snapshot_evidence_id:str; snapshot_domain:str; related_checklist_item_id:str; related_approval_packet_artifact_id:str; related_manifest_audit_id:str; related_export_package_id:str; related_support_artifact_ids:tuple[str,...]; evidence_source_reference:str; evidence_kind:str; evidence_hash:str; evidence_status:str; snapshot_inclusion_status:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class SnapshotFindingRecord:
    finding_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class SnapshotLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceApprovalChecklistEvidenceSnapshotSpec:
    phase:str; objective:str; snapshot_bundle_id:str; source_checklist_id:str; source_approval_packet_id:str; deterministic_timestamp:str; snapshot_domains:tuple[str,...]; snapshot_evidence_records:tuple[SnapshotEvidenceRecord,...]; snapshot_findings:tuple[SnapshotFindingRecord,...]; snapshot_limitation_register:tuple[SnapshotLimitationRecord,...]; non_authorization_notices:tuple[str,...]; safety_flags:Phase80SafetyFlags=Phase80SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceApprovalChecklistEvidenceSnapshotFixtureInput:
    fixture_id:str; snapshot_bundle_id:str; source_checklist_id:str; source_approval_packet_id:str; source_manifest_audit_id:str; source_export_package_id:str; source_final_readiness_bundle_id:str; deterministic_timestamp:str; checklist_present:bool; checklist_classification:str; approval_packet_present:bool; approval_packet_classification:str; manifest_audit_present:bool; export_package_present:bool; final_readiness_bundle_present:bool; non_authorization_notices:tuple[str,...]; reviewer_acknowledgement_present:bool; snapshot_evidence_records:tuple[SnapshotEvidenceRecord,...]; hidden_unresolved_blocker:bool; hidden_unresolved_limitation:bool; expired_waiver_unresolved:bool; revoked_waiver_unresolved:bool; overdue_sla_unresolved:bool; dependency_audit_unresolved:bool; safety_review_unresolved:bool; traceability_gap:bool; stale_evidence:bool=False; redacted_evidence_requires_review:bool=False; reference_only_evidence_missing_limitation:bool=False; synthetic_only_evidence_requires_review:bool=False; unsafe_waiver_attempt_unresolved:bool=False; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_snapshot_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_snapshot_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceApprovalChecklistEvidenceSnapshotReport:
    fixture_id:str; spec:XamanGovernanceApprovalChecklistEvidenceSnapshotSpec; final_snapshot_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
