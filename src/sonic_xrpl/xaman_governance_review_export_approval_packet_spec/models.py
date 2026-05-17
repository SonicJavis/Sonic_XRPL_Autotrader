from __future__ import annotations
from dataclasses import dataclass
from typing import Any
APPROVAL_PACKET_NOT_READY='APPROVAL_PACKET_NOT_READY'; APPROVAL_PACKET_REVIEW_REQUIRED='APPROVAL_PACKET_REVIEW_REQUIRED'; APPROVAL_PACKET_SPEC_REVIEW_READY='APPROVAL_PACKET_SPEC_REVIEW_READY'; APPROVAL_PACKET_BLOCKED='APPROVAL_PACKET_BLOCKED'; APPROVAL_PACKET_INCOMPLETE='APPROVAL_PACKET_INCOMPLETE'
APPROVAL_PACKET_DOMAINS=('EXPORT_PACKAGE','MANIFEST_AUDIT','FINAL_READINESS_BUNDLE','SIGNOFF_MATRIX','EVIDENCE_ATTESTATION','REVIEW_WORKFLOW','ESCALATION_SLA','EXCEPTION_WAIVER_REGISTER','LIMITATION_REGISTER','REVIEWER_ACKNOWLEDGEMENTS','NON_AUTHORIZATION_NOTICES','SAFETY_GUARDS','DEPENDENCY_AUDIT','POLICY_DOCS','TRACEABILITY_MAP')
NON_AUTHORIZATION_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime approval service authorized','no download/API/UI route authorized','no safety bypass authorized')
REQUIRED_ROLES=('SECURITY_REVIEWER','XRPL_PROTOCOL_REVIEWER','XAMAN_REVIEWER','SUPPLY_CHAIN_REVIEWER','RISK_REVIEWER','AUDIT_REVIEWER','OPERATOR_REVIEWER','FINAL_GOVERNANCE_OWNER')
@dataclass(frozen=True)
class Phase78SafetyFlags:
    spec_only:bool=True; approval_packet_spec_only:bool=True; runtime_approval_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class ApprovalArtifactReference:
    approval_artifact_id:str; source_phase_number:str; source_artifact_type:str; source_reference:str; source_hash:str; required_classification:str; inclusion_status:str; audit_status:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class ReviewerAcknowledgementRecord:
    acknowledgement_id:str; reviewer_role:str; reviewer_domain:str; related_artifact_id:str; acknowledgement_status:str; acknowledgement_limitation:str; non_authorization_statement:str; required_evidence_references:tuple[str,...]; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class ApprovalLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceReviewExportApprovalPacketSpec:
    phase:str; objective:str; approval_packet_id:str; source_export_package_id:str; source_manifest_audit_id:str; deterministic_timestamp:str; approval_packet_domains:tuple[str,...]; artifact_references:tuple[ApprovalArtifactReference,...]; reviewer_acknowledgements:tuple[ReviewerAcknowledgementRecord,...]; non_authorization_notices:tuple[str,...]; approval_limitation_register:tuple[ApprovalLimitationRecord,...]; safety_flags:Phase78SafetyFlags=Phase78SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceReviewExportApprovalPacketFixtureInput:
    fixture_id:str; approval_packet_id:str; source_export_package_id:str; source_manifest_audit_id:str; deterministic_timestamp:str; export_package_present:bool; manifest_audit_present:bool; export_classification:str; manifest_audit_classification:str; artifact_references:tuple[ApprovalArtifactReference,...]; reviewer_acknowledgements:tuple[ReviewerAcknowledgementRecord,...]; unresolved_blocker_hidden:bool; unresolved_limitation_hidden:bool; expired_waiver_unresolved:bool; revoked_waiver_unresolved:bool; overdue_sla_unresolved:bool; unsafe_waiver_attempt_unresolved:bool; dependency_audit_unresolved:bool; safety_review_unresolved:bool; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_approval_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_approval_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceReviewExportApprovalPacketReport:
    fixture_id:str; spec:XamanGovernanceReviewExportApprovalPacketSpec; final_packet_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
