from __future__ import annotations
from dataclasses import dataclass
from typing import Any
DIGEST_NOT_READY='DIGEST_NOT_READY'; DIGEST_REVIEW_REQUIRED='DIGEST_REVIEW_REQUIRED'; DIGEST_SPEC_REVIEW_READY='DIGEST_SPEC_REVIEW_READY'; DIGEST_BLOCKED='DIGEST_BLOCKED'; DIGEST_INCOMPLETE='DIGEST_INCOMPLETE'
DIGEST_DOMAINS=('EVIDENCE_SNAPSHOT','APPROVAL_CHECKLIST','APPROVAL_PACKET','MANIFEST_AUDIT','EXPORT_PACKAGE','FINAL_READINESS_BUNDLE','NON_AUTHORIZATION_NOTICES','REVIEWER_ACKNOWLEDGEMENTS','UNRESOLVED_BLOCKERS','UNRESOLVED_LIMITATIONS','EVIDENCE_QUALITY','WAIVER_STATUS','SLA_STATUS','DEPENDENCY_AUDIT','SAFETY_REVIEW','TRACEABILITY_MAP','POLICY_DOCS')
REQUIRED_NOTICES=('no payload creation authorized','no Xaman API call authorized','no signing authorized','no submission authorized','no autofill authorized','no wallet material handling authorized','no testnet execution authorized','no live execution authorized','no runtime digest service authorized','no download/API/UI route authorized','no safety bypass authorized')
@dataclass(frozen=True)
class Phase81SafetyFlags:
    spec_only:bool=True; snapshot_review_digest_spec_only:bool=True; runtime_digest_service_allowed:bool=False; download_service_allowed:bool=False; api_route_allowed:bool=False; dashboard_ui_allowed:bool=False; safety_bypass_allowed:bool=False; testnet_execution_allowed:bool=False; xaman_payload_creation_allowed:bool=False; xaman_api_calls_allowed:bool=False; xaman_sdk_dependency_allowed:bool=False; signing_allowed:bool=False; submission_allowed:bool=False; autofill_allowed:bool=False; wallet_material_allowed:bool=False; live_execution_allowed:bool=False; runtime_mutation_allowed:bool=False
@dataclass(frozen=True)
class DigestSectionRecord:
    digest_section_id:str; digest_domain:str; related_snapshot_record_id:str; related_checklist_item_id:str; related_approval_packet_id:str; related_support_artifact_ids:tuple[str,...]; section_title:str; section_summary:str; evidence_count:int; blocker_count:int; limitation_count:int; reviewer_visibility:str; digest_status:str; severity:str; limitation_notes:str; safety_flags:tuple[str,...]
@dataclass(frozen=True)
class DigestFindingRecord:
    finding_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class DigestLimitationRecord:
    limitation_id:str; category:str; related_item_id:str; severity:str; summary:str
@dataclass(frozen=True)
class XamanGovernanceSnapshotReviewDigestSpec:
    phase:str; objective:str; digest_bundle_id:str; source_snapshot_id:str; source_checklist_id:str; deterministic_timestamp:str; digest_domains:tuple[str,...]; digest_sections:tuple[DigestSectionRecord,...]; digest_findings:tuple[DigestFindingRecord,...]; digest_limitation_register:tuple[DigestLimitationRecord,...]; non_authorization_notices:tuple[str,...]; safety_flags:Phase81SafetyFlags=Phase81SafetyFlags()
@dataclass(frozen=True)
class XamanGovernanceSnapshotReviewDigestFixtureInput:
    fixture_id:str; digest_bundle_id:str; source_snapshot_id:str; source_checklist_id:str; source_approval_packet_id:str; deterministic_timestamp:str; snapshot_present:bool; snapshot_classification:str; checklist_present:bool; checklist_classification:str; non_authorization_notices:tuple[str,...]; reviewer_ack_summary_present:bool; digest_sections:tuple[DigestSectionRecord,...]; hidden_unresolved_blocker:bool; hidden_unresolved_limitation:bool; dependency_audit_summary_gap:bool; safety_review_summary_gap:bool; traceability_gap:bool; stale_evidence_summary_gap:bool=False; redacted_evidence_summary_gap:bool=False; reference_only_evidence_summary_gap:bool=False; synthetic_only_evidence_summary_gap:bool=False; invalid_xaman_payload_approval_marker:bool=False; invalid_wallet_material_approval_marker:bool=False; invalid_signing_submission_autofill_approval_marker:bool=False; invalid_testnet_live_execution_approval_marker:bool=False; invalid_runtime_digest_service_marker:bool=False; invalid_download_service_marker:bool=False; invalid_api_ui_digest_route_marker:bool=False; invalid_safety_bypass_marker:bool=False
@dataclass(frozen=True)
class XamanGovernanceSnapshotReviewDigestReport:
    fixture_id:str; spec:XamanGovernanceSnapshotReviewDigestSpec; final_digest_classification:str; validation_errors:tuple[str,...]; blockers:tuple[str,...]
def jsonable(v:Any)->Any:
    if hasattr(v,'__dataclass_fields__'): return {k:jsonable(getattr(v,k)) for k in v.__dataclass_fields__}
    if isinstance(v,tuple): return [jsonable(i) for i in v]
    if isinstance(v,list): return [jsonable(i) for i in v]
    if isinstance(v,dict): return {str(k):jsonable(x) for k,x in v.items()}
    return v
