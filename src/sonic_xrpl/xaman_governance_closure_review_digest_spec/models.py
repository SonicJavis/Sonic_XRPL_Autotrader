from __future__ import annotations
from dataclasses import dataclass
from typing import Any
CLOSURE_DIGEST_NOT_READY='CLOSURE_DIGEST_NOT_READY'; CLOSURE_DIGEST_REVIEW_REQUIRED='CLOSURE_DIGEST_REVIEW_REQUIRED'; CLOSURE_DIGEST_SPEC_REVIEW_READY='CLOSURE_DIGEST_SPEC_REVIEW_READY'; CLOSURE_DIGEST_BLOCKED='CLOSURE_DIGEST_BLOCKED'; CLOSURE_DIGEST_INCOMPLETE='CLOSURE_DIGEST_INCOMPLETE'
CLOSURE_DIGEST_DOMAINS=('RESOLUTION_EVIDENCE_CLOSURE','CLOSURE_EVIDENCE','EVIDENCE_SUFFICIENCY','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','NON_AUTHORIZATION_CONFIRMATIONS','REVIEWER_OWNERSHIP','DEFERRALS','REJECTIONS','SUPERSESSIONS','DEPENDENCY_AUDIT','SAFETY_REVIEW','EXCEPTION_WAIVER_REGISTER','ESCALATION_SLA','RESPONSE_RESOLUTION_REGISTER','DIGEST_REVIEW_RESPONSE','SNAPSHOT_REVIEW_DIGEST','EVIDENCE_SNAPSHOT','APPROVAL_CHECKLIST','POLICY_DOCS','TRACEABILITY_MAP')
REQUIRED_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime closure digest service authorized','no download/API/UI route authorized','no safety bypass authorized')
@dataclass(frozen=True)
class Phase85SafetyFlags:
    spec_only:bool=True; closure_review_digest_spec_only:bool=True; runtime_closure_digest_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class ClosureDigestSectionRecord:
    closure_digest_section_id:str; digest_domain:str; related_closure_evidence_id:str; related_resolution_record_id:str; related_response_record_id:str; related_digest_id:str; related_snapshot_id:str; related_checklist_item_id:str; related_approval_packet_id:str; related_support_artifact_ids:tuple[str,...]; section_title:str; section_summary:str; evidence_count:int; sufficient_evidence_count:int; insufficient_evidence_count:int; blocker_count:int; limitation_count:int; reviewer_visibility:str; digest_status:str; severity:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class ClosureDigestFindingRecord:
    finding_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class ClosureDigestLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceClosureReviewDigestSpec:
    phase:str; objective:str; closure_digest_bundle_id:str; source_closure_bundle_id:str; source_resolution_register_id:str; deterministic_timestamp:str; closure_digest_domains:tuple[str,...]; closure_digest_sections:tuple[ClosureDigestSectionRecord,...]; closure_digest_findings:tuple[ClosureDigestFindingRecord,...]; closure_digest_limitation_register:tuple[ClosureDigestLimitationRecord,...]; non_authorization_notices:tuple[str,...]; safety_flags:Phase85SafetyFlags=Phase85SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceClosureReviewDigestFixtureInput:
    fixture_id:str; closure_digest_bundle_id:str; source_closure_bundle_id:str; source_resolution_register_id:str; deterministic_timestamp:str; closure_bundle_present:bool; closure_bundle_classification:str; resolution_register_classification:str; non_authorization_notices:tuple[str,...]; reviewer_ownership_summary_present:bool; closure_digest_sections:tuple[ClosureDigestSectionRecord,...]; missing_closure_evidence_summary:bool=False; missing_resolution_register_summary:bool=False; missing_response_summary:bool=False; missing_digest_snapshot_checklist_summary:bool=False; hidden_unresolved_blocker:bool=False; hidden_unresolved_limitation:bool=False; dependency_audit_closure_summary_gap:bool=False; safety_review_closure_summary_gap:bool=False; traceability_gap:bool=False; stale_closure_evidence_summary_gap:bool=False; redacted_closure_evidence_summary_gap:bool=False; reference_only_closure_evidence_summary_gap:bool=False; synthetic_only_closure_evidence_summary_gap:bool=False; missing_non_authorization_summary:bool=False; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_closure_digest_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_closure_digest_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceClosureReviewDigestReport:
    fixture_id:str; spec:XamanGovernanceClosureReviewDigestSpec; final_closure_digest_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
