from __future__ import annotations
from dataclasses import dataclass
from typing import Any
CHECKLIST_NOT_READY='CHECKLIST_NOT_READY'; CHECKLIST_REVIEW_REQUIRED='CHECKLIST_REVIEW_REQUIRED'; CHECKLIST_SPEC_REVIEW_READY='CHECKLIST_SPEC_REVIEW_READY'; CHECKLIST_BLOCKED='CHECKLIST_BLOCKED'; CHECKLIST_INCOMPLETE='CHECKLIST_INCOMPLETE'
CHECKLIST_DOMAINS=('APPROVAL_PACKET_COMPLETENESS','REVIEWER_ACKNOWLEDGEMENTS','NON_AUTHORIZATION_NOTICES','MANIFEST_AUDIT','EXPORT_PACKAGE','FINAL_READINESS_BUNDLE','SIGNOFF_MATRIX','EVIDENCE_ATTESTATION','REVIEW_WORKFLOW','ESCALATION_SLA','EXCEPTION_WAIVER_REGISTER','LIMITATION_REGISTER','SAFETY_GUARDS','DEPENDENCY_AUDIT','POLICY_DOCS','TRACEABILITY_MAP')
REQUIRED_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime checklist service authorized','no download/API/UI route authorized','no safety bypass authorized')
REQUIRED_ROLES=('SECURITY_REVIEWER','XRPL_PROTOCOL_REVIEWER','XAMAN_REVIEWER','SUPPLY_CHAIN_REVIEWER','RISK_REVIEWER','AUDIT_REVIEWER','OPERATOR_REVIEWER','FINAL_GOVERNANCE_OWNER')
@dataclass(frozen=True)
class Phase79SafetyFlags:
    spec_only:bool=True; review_checklist_spec_only:bool=True; runtime_checklist_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class ChecklistItemRecord:
    checklist_item_id:str; checklist_domain:str; related_approval_packet_artifact_id:str; related_manifest_audit_id:str; related_export_package_id:str; related_support_artifact_ids:tuple[str,...]; reviewer_role:str; required_evidence_reference:str; checklist_question:str; expected_safe_answer:str; actual_fixture_answer:str; checklist_status:str; finding_severity:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class ChecklistFindingRecord:
    finding_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class ChecklistLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceApprovalPacketReviewChecklistSpec:
    phase:str; objective:str; checklist_bundle_id:str; source_approval_packet_id:str; deterministic_timestamp:str; checklist_domains:tuple[str,...]; checklist_items:tuple[ChecklistItemRecord,...]; checklist_findings:tuple[ChecklistFindingRecord,...]; checklist_limitation_register:tuple[ChecklistLimitationRecord,...]; non_authorization_notices:tuple[str,...]; safety_flags:Phase79SafetyFlags=Phase79SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceApprovalPacketReviewChecklistFixtureInput:
    fixture_id:str; checklist_bundle_id:str; source_approval_packet_id:str; source_manifest_audit_id:str; source_export_package_id:str; source_final_readiness_bundle_id:str; deterministic_timestamp:str; approval_packet_present:bool; approval_packet_classification:str; manifest_audit_present:bool; manifest_audit_classification:str; export_package_present:bool; final_readiness_bundle_present:bool; reviewer_roles:tuple[str,...]; non_authorization_notices:tuple[str,...]; checklist_items:tuple[ChecklistItemRecord,...]; hidden_unresolved_blocker:bool; hidden_unresolved_limitation:bool; expired_waiver_unresolved:bool; revoked_waiver_unresolved:bool; overdue_sla_unresolved:bool; dependency_audit_unresolved:bool; safety_review_unresolved:bool; traceability_gap:bool; ambiguous_non_authorization_wording:bool=False; unsafe_waiver_attempt_unresolved:bool=False; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_checklist_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_checklist_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceApprovalPacketReviewChecklistReport:
    fixture_id:str; spec:XamanGovernanceApprovalPacketReviewChecklistSpec; final_checklist_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
