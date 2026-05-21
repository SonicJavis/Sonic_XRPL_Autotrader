from __future__ import annotations
from dataclasses import dataclass
from typing import Any
CLOSURE_RESPONSE_RESOLUTION_REGISTER_NOT_READY='CLOSURE_RESPONSE_RESOLUTION_REGISTER_NOT_READY'; CLOSURE_RESPONSE_RESOLUTION_REVIEW_REQUIRED='CLOSURE_RESPONSE_RESOLUTION_REVIEW_REQUIRED'; CLOSURE_RESPONSE_RESOLUTION_REGISTER_SPEC_REVIEW_READY='CLOSURE_RESPONSE_RESOLUTION_REGISTER_SPEC_REVIEW_READY'; CLOSURE_RESPONSE_RESOLUTION_BLOCKED='CLOSURE_RESPONSE_RESOLUTION_BLOCKED'; CLOSURE_RESPONSE_RESOLUTION_INCOMPLETE='CLOSURE_RESPONSE_RESOLUTION_INCOMPLETE'
RESPONSE_DOMAINS=('CLOSURE_REVIEW_DIGEST','CLOSURE_DIGEST_FINDINGS','CLOSURE_DIGEST_SECTIONS','EVIDENCE_SUFFICIENCY','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','NON_AUTHORIZATION_CONFIRMATIONS','REVIEWER_OWNERSHIP','DEFERRALS','REJECTIONS','SUPERSESSIONS','DEPENDENCY_AUDIT','SAFETY_REVIEW','EXCEPTION_WAIVER_REGISTER','ESCALATION_SLA','RESOLUTION_EVIDENCE_CLOSURE','RESPONSE_RESOLUTION_REGISTER','DIGEST_REVIEW_RESPONSE','SNAPSHOT_REVIEW_DIGEST','POLICY_DOCS','TRACEABILITY_MAP')
REQUIRED_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime closure response resolution service authorized','no download/API/UI route authorized','no safety bypass authorized')
@dataclass(frozen=True)
class Phase87SafetyFlags:
    spec_only:bool=True; closure_response_resolution_register_spec_only:bool=True; runtime_closure_response_resolution_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class ClosureResponseResolutionRecord:
    closure_response_resolution_id:str; resolution_domain:str; related_phase85_digest_item_id:str; related_phase84_closure_evidence_id:str; related_phase83_resolution_record_id:str; related_phase82_response_record_id:str; related_phase81_digest_id:str; related_phase80_snapshot_id:str; related_phase79_checklist_item_id:str; related_phase78_approval_packet_id:str; related_phase70_77_support_artifact_ids:tuple[str,...]; reviewer_role:str; resolution_category:str; resolution_status:str; resolution_summary:str; required_follow_up_evidence_references:tuple[str,...]; evidence_sufficiency_response:str; unresolved_blocker_references:tuple[str,...]; unresolved_limitation_references:tuple[str,...]; non_authorization_confirmation:bool; closure_condition:str; deferral_reason:str; rejection_reason:str; superseded_by_resolution_id:str; severity:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class ClosureResponseResolutionFindingRecord:
    finding_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class ClosureResponseResolutionLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceClosureResponseResolutionRegisterSpec:
    phase:str; objective:str; closure_response_resolution_register_id:str; source_closure_digest_response_bundle_id:str; source_closure_bundle_id:str; deterministic_timestamp:str; resolution_domains:tuple[str,...]; resolution_records:tuple[ClosureResponseResolutionRecord,...]; resolution_findings:tuple[ClosureResponseResolutionFindingRecord,...]; resolution_limitation_register:tuple[ClosureResponseResolutionLimitationRecord,...]; non_authorization_notices:tuple[str,...]; safety_flags:Phase87SafetyFlags=Phase87SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceClosureResponseResolutionRegisterFixtureInput:
    fixture_id:str; closure_response_resolution_register_id:str; source_closure_digest_response_bundle_id:str; source_closure_bundle_id:str; deterministic_timestamp:str; closure_digest_classification:str; closure_classification:str; resolution_records:tuple[ClosureResponseResolutionRecord,...]; non_authorization_notices:tuple[str,...]; missing_closure_digest_response:bool=False; incomplete_closure_digest_response:bool=False; rejected_closure_digest_response_unresolved:bool=False; deferred_blocker_without_limitation:bool=False; superseded_response_missing_replacement:bool=False; missing_non_authorization_confirmation:bool=False; missing_reviewer_response:bool=False; missing_follow_up_evidence_reference:bool=False; missing_evidence_sufficiency_response:bool=False; unresolved_blocker_lacks_response:bool=False; unresolved_limitation_lacks_response:bool=False; stale_closure_evidence_response_unresolved:bool=False; redacted_closure_evidence_response_unresolved:bool=False; reference_only_closure_evidence_response_unresolved:bool=False; synthetic_only_closure_evidence_response_unresolved:bool=False; dependency_audit_response_unresolved:bool=False; safety_review_response_unresolved:bool=False; traceability_gap:bool=False; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_closure_digest_response_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_closure_digest_response_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceClosureResponseResolutionRegisterReport:
    fixture_id:str; spec:XamanGovernanceClosureResponseResolutionRegisterSpec; final_resolution_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
