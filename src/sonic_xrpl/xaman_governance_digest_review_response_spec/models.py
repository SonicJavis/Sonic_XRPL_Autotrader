from __future__ import annotations
from dataclasses import dataclass
from typing import Any
RESPONSE_BUNDLE_NOT_READY='RESPONSE_BUNDLE_NOT_READY'; RESPONSE_BUNDLE_REVIEW_REQUIRED='RESPONSE_BUNDLE_REVIEW_REQUIRED'; RESPONSE_BUNDLE_SPEC_REVIEW_READY='RESPONSE_BUNDLE_SPEC_REVIEW_READY'; RESPONSE_BUNDLE_BLOCKED='RESPONSE_BUNDLE_BLOCKED'; RESPONSE_BUNDLE_INCOMPLETE='RESPONSE_BUNDLE_INCOMPLETE'
RESPONSE_DOMAINS=('DIGEST_FINDINGS','DIGEST_SECTIONS','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','EVIDENCE_QUALITY','NON_AUTHORIZATION_NOTICES','REVIEWER_ACKNOWLEDGEMENTS','APPROVAL_CHECKLIST','APPROVAL_PACKET','MANIFEST_AUDIT','EXPORT_PACKAGE','FINAL_READINESS_BUNDLE','EXCEPTION_WAIVER_REGISTER','ESCALATION_SLA','DEPENDENCY_AUDIT','SAFETY_REVIEW','POLICY_DOCS','TRACEABILITY_MAP')
REQUIRED_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime response service authorized','no download/API/UI route authorized','no safety bypass authorized')
@dataclass(frozen=True)
class Phase82SafetyFlags:
    spec_only:bool=True; digest_review_response_spec_only:bool=True; runtime_response_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class ResponseRecord:
    response_id:str; response_domain:str; related_digest_id:str; related_snapshot_id:str; related_checklist_item_id:str; related_approval_packet_id:str; related_support_artifact_ids:tuple[str,...]; reviewer_role:str; response_category:str; response_summary:str; follow_up_evidence_reference:str; resolution_intent:str; non_authorization_confirmation:bool; response_status:str; severity:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class ResponseFindingRecord:
    finding_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class ResponseLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceDigestReviewResponseSpec:
    phase:str; objective:str; response_bundle_id:str; source_digest_bundle_id:str; source_snapshot_id:str; deterministic_timestamp:str; response_domains:tuple[str,...]; response_records:tuple[ResponseRecord,...]; response_findings:tuple[ResponseFindingRecord,...]; response_limitation_register:tuple[ResponseLimitationRecord,...]; non_authorization_notices:tuple[str,...]; safety_flags:Phase82SafetyFlags=Phase82SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceDigestReviewResponseFixtureInput:
    fixture_id:str; response_bundle_id:str; source_digest_bundle_id:str; source_snapshot_id:str; deterministic_timestamp:str; digest_classification:str; snapshot_classification:str; response_records:tuple[ResponseRecord,...]; non_authorization_notices:tuple[str,...]; missing_digest_response:bool=False; incomplete_digest_response:bool=False; rejected_digest_response:bool=False; deferred_blocker_without_limitation:bool=False; missing_non_authorization_confirmation:bool=False; missing_security_reviewer_response:bool=False; missing_follow_up_evidence_reference:bool=False; unresolved_blocker_lacks_response:bool=False; unresolved_limitation_lacks_response:bool=False; stale_evidence_response_unresolved:bool=False; redacted_evidence_response_unresolved:bool=False; reference_only_evidence_response_unresolved:bool=False; synthetic_only_evidence_response_unresolved:bool=False; dependency_audit_response_unresolved:bool=False; safety_review_response_unresolved:bool=False; traceability_gap:bool=False; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_response_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_response_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceDigestReviewResponseReport:
    fixture_id:str; spec:XamanGovernanceDigestReviewResponseSpec; final_response_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
