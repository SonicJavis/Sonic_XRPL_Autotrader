from __future__ import annotations
from dataclasses import dataclass
from typing import Any
RESOLUTION_REGISTER_NOT_READY='RESOLUTION_REGISTER_NOT_READY'; RESOLUTION_REGISTER_REVIEW_REQUIRED='RESOLUTION_REGISTER_REVIEW_REQUIRED'; RESOLUTION_REGISTER_SPEC_REVIEW_READY='RESOLUTION_REGISTER_SPEC_REVIEW_READY'; RESOLUTION_REGISTER_BLOCKED='RESOLUTION_REGISTER_BLOCKED'; RESOLUTION_REGISTER_INCOMPLETE='RESOLUTION_REGISTER_INCOMPLETE'
RESOLUTION_DOMAINS=('DIGEST_REVIEW_RESPONSES','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','FOLLOW_UP_EVIDENCE','NON_AUTHORIZATION_CONFIRMATIONS','REVIEWER_OWNERSHIP','DEFERRALS','REJECTIONS','SUPERSESSIONS','DEPENDENCY_AUDIT','SAFETY_REVIEW','EXCEPTION_WAIVER_REGISTER','ESCALATION_SLA','APPROVAL_CHECKLIST','EVIDENCE_SNAPSHOT','SNAPSHOT_REVIEW_DIGEST','POLICY_DOCS','TRACEABILITY_MAP')
REQUIRED_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime resolution service authorized','no download/API/UI route authorized','no safety bypass authorized')
@dataclass(frozen=True)
class Phase83SafetyFlags:
    spec_only:bool=True; response_resolution_register_spec_only:bool=True; runtime_resolution_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class ResolutionRecord:
    resolution_id:str; resolution_domain:str; related_response_record_id:str; related_digest_id:str; related_snapshot_id:str; related_checklist_item_id:str; related_approval_packet_id:str; related_support_artifact_ids:tuple[str,...]; owner_role:str; resolution_category:str; resolution_status:str; resolution_summary:str; follow_up_evidence_references:tuple[str,...]; unresolved_blocker_references:tuple[str,...]; unresolved_limitation_references:tuple[str,...]; non_authorization_confirmation:bool; closure_condition:str; deferral_reason:str; rejection_reason:str; superseded_by_resolution_id:str; severity:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class ResolutionFindingRecord:
    finding_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class ResolutionLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceResponseResolutionRegisterSpec:
    phase:str; objective:str; resolution_register_id:str; source_response_bundle_id:str; source_digest_bundle_id:str; deterministic_timestamp:str; resolution_domains:tuple[str,...]; resolution_records:tuple[ResolutionRecord,...]; resolution_findings:tuple[ResolutionFindingRecord,...]; resolution_limitation_register:tuple[ResolutionLimitationRecord,...]; non_authorization_notices:tuple[str,...]; safety_flags:Phase83SafetyFlags=Phase83SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceResponseResolutionRegisterFixtureInput:
    fixture_id:str; resolution_register_id:str; source_response_bundle_id:str; source_digest_bundle_id:str; deterministic_timestamp:str; response_classification:str; digest_classification:str; resolution_records:tuple[ResolutionRecord,...]; non_authorization_notices:tuple[str,...]; missing_resolution_record:bool=False; incomplete_resolution_record:bool=False; rejected_resolution_unresolved:bool=False; deferred_blocker_without_limitation:bool=False; superseded_resolution_missing_replacement:bool=False; missing_non_authorization_confirmation:bool=False; missing_owner:bool=False; missing_follow_up_evidence_reference:bool=False; unresolved_blocker_lacks_resolution:bool=False; unresolved_limitation_lacks_resolution:bool=False; stale_evidence_resolution_unresolved:bool=False; redacted_evidence_resolution_unresolved:bool=False; reference_only_evidence_resolution_unresolved:bool=False; synthetic_only_evidence_resolution_unresolved:bool=False; dependency_audit_resolution_unresolved:bool=False; safety_review_resolution_unresolved:bool=False; traceability_gap:bool=False; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_resolution_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_resolution_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceResponseResolutionRegisterReport:
    fixture_id:str; spec:XamanGovernanceResponseResolutionRegisterSpec; final_resolution_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
