from __future__ import annotations
from dataclasses import dataclass
from typing import Any
CLOSURE_BUNDLE_NOT_READY='CLOSURE_BUNDLE_NOT_READY'; CLOSURE_BUNDLE_REVIEW_REQUIRED='CLOSURE_BUNDLE_REVIEW_REQUIRED'; CLOSURE_BUNDLE_SPEC_REVIEW_READY='CLOSURE_BUNDLE_SPEC_REVIEW_READY'; CLOSURE_BUNDLE_BLOCKED='CLOSURE_BUNDLE_BLOCKED'; CLOSURE_BUNDLE_INCOMPLETE='CLOSURE_BUNDLE_INCOMPLETE'
CLOSURE_DOMAINS=('RESPONSE_RESOLUTION_REGISTER','CLOSURE_EVIDENCE','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','FOLLOW_UP_EVIDENCE','NON_AUTHORIZATION_CONFIRMATIONS','REVIEWER_OWNERSHIP','DEFERRALS','REJECTIONS','SUPERSESSIONS','DEPENDENCY_AUDIT','SAFETY_REVIEW','EXCEPTION_WAIVER_REGISTER','ESCALATION_SLA','APPROVAL_CHECKLIST','EVIDENCE_SNAPSHOT','SNAPSHOT_REVIEW_DIGEST','DIGEST_REVIEW_RESPONSE','POLICY_DOCS','TRACEABILITY_MAP')
REQUIRED_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime closure service authorized','no download/API/UI route authorized','no safety bypass authorized')
@dataclass(frozen=True)
class Phase84SafetyFlags:
    spec_only:bool=True; resolution_evidence_closure_spec_only:bool=True; runtime_closure_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class ClosureEvidenceRecord:
    closure_evidence_id:str; closure_domain:str; related_resolution_record_id:str; related_response_record_id:str; related_digest_id:str; related_snapshot_id:str; related_checklist_item_id:str; related_approval_packet_id:str; related_support_artifact_ids:tuple[str,...]; owner_role:str; reviewer_role:str; evidence_category:str; evidence_status:str; evidence_sufficiency_status:str; evidence_summary:str; source_evidence_references:tuple[str,...]; unresolved_blocker_references:tuple[str,...]; unresolved_limitation_references:tuple[str,...]; non_authorization_confirmation:bool; closure_condition:str; deferral_reason:str; rejection_reason:str; superseded_by_closure_evidence_id:str; severity:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class ClosureFindingRecord:
    finding_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class ClosureLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceResolutionEvidenceClosureSpec:
    phase:str; objective:str; closure_bundle_id:str; source_resolution_register_id:str; source_response_bundle_id:str; deterministic_timestamp:str; closure_domains:tuple[str,...]; closure_evidence_records:tuple[ClosureEvidenceRecord,...]; closure_findings:tuple[ClosureFindingRecord,...]; closure_limitation_register:tuple[ClosureLimitationRecord,...]; non_authorization_notices:tuple[str,...]; safety_flags:Phase84SafetyFlags=Phase84SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceResolutionEvidenceClosureFixtureInput:
    fixture_id:str; closure_bundle_id:str; source_resolution_register_id:str; source_response_bundle_id:str; deterministic_timestamp:str; resolution_register_classification:str; response_classification:str; closure_evidence_records:tuple[ClosureEvidenceRecord,...]; non_authorization_notices:tuple[str,...]; missing_closure_evidence:bool=False; incomplete_closure_evidence:bool=False; rejected_closure_evidence_unresolved:bool=False; deferred_closure_without_limitation:bool=False; superseded_closure_missing_replacement:bool=False; missing_non_authorization_confirmation:bool=False; missing_owner:bool=False; missing_reviewer:bool=False; missing_source_evidence_reference:bool=False; unresolved_blocker_lacks_closure_evidence:bool=False; unresolved_limitation_lacks_closure_evidence:bool=False; stale_evidence_closure_unresolved:bool=False; redacted_evidence_closure_unresolved:bool=False; reference_only_evidence_closure_unresolved:bool=False; synthetic_only_evidence_closure_unresolved:bool=False; dependency_audit_closure_unresolved:bool=False; safety_review_closure_unresolved:bool=False; traceability_gap:bool=False; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_closure_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_closure_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceResolutionEvidenceClosureReport:
    fixture_id:str; spec:XamanGovernanceResolutionEvidenceClosureSpec; final_closure_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
