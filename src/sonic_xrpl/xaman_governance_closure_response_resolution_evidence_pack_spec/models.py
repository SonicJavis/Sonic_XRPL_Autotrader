from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVIDENCE_PACK_NOT_READY = "EVIDENCE_PACK_NOT_READY"
EVIDENCE_PACK_REVIEW_REQUIRED = "EVIDENCE_PACK_REVIEW_REQUIRED"
EVIDENCE_PACK_SPEC_REVIEW_READY = "EVIDENCE_PACK_SPEC_REVIEW_READY"
EVIDENCE_PACK_BLOCKED = "EVIDENCE_PACK_BLOCKED"
EVIDENCE_PACK_INCOMPLETE = "EVIDENCE_PACK_INCOMPLETE"

EVIDENCE_PACK_DOMAINS = (
    "CLOSURE_RESPONSE_RESOLUTION_REGISTER",
    "CLOSURE_RESPONSE_RESOLUTION_RECORDS",
    "FOLLOW_UP_EVIDENCE",
    "EVIDENCE_COMPLETENESS",
    "EVIDENCE_SUFFICIENCY_RESOLUTION",
    "UNRESOLVED_BLOCKERS",
    "UNRESOLVED_LIMITATIONS",
    "NON_AUTHORIZATION_CONFIRMATIONS",
    "OWNER_REVIEWER_MAPPING",
    "DEFERRALS",
    "REJECTIONS",
    "SUPERSESSIONS",
    "DEPENDENCY_AUDIT",
    "SAFETY_REVIEW",
    "CLOSURE_DIGEST_RESPONSE",
    "CLOSURE_REVIEW_DIGEST",
    "RESOLUTION_EVIDENCE_CLOSURE",
    "RESPONSE_RESOLUTION_REGISTER",
    "POLICY_DOCS",
    "TRACEABILITY_MAP",
)

REQUIRED_NOTICES = (
    "no payload creation authorized",
    "no Xaman API call authorized",
    "no signing authorized",
    "no submission authorized",
    "no autofill authorized",
    "no wallet material handling authorized",
    "no testnet execution authorized",
    "no live execution authorized",
    "no runtime closure response resolution evidence pack service authorized",
    "no download/API/UI route authorized",
    "no safety bypass authorized",
)


@dataclass(frozen=True)
class Phase88SafetyFlags:
    spec_only: bool = True
    closure_response_resolution_evidence_pack_spec_only: bool = True
    runtime_closure_response_resolution_evidence_pack_service_allowed: bool = False
    download_service_allowed: bool = False
    api_route_allowed: bool = False
    dashboard_ui_allowed: bool = False
    safety_bypass_allowed: bool = False
    testnet_execution_allowed: bool = False
    xaman_payload_creation_allowed: bool = False
    xaman_api_calls_allowed: bool = False
    xaman_sdk_dependency_allowed: bool = False
    signing_allowed: bool = False
    submission_allowed: bool = False
    autofill_allowed: bool = False
    wallet_material_allowed: bool = False
    live_execution_allowed: bool = False
    runtime_mutation_allowed: bool = False


@dataclass(frozen=True)
class EvidencePackRecord:
    evidence_pack_id: str
    evidence_pack_domain: str
    related_phase87_closure_response_resolution_id: str
    related_phase86_closure_digest_response_id: str
    related_phase85_digest_item_id: str
    related_phase84_closure_evidence_id: str
    related_phase83_resolution_record_id: str
    related_phase82_response_record_id: str
    related_phase81_digest_id: str
    related_phase80_snapshot_id: str
    related_phase79_checklist_item_id: str
    related_phase78_approval_packet_id: str
    related_phase70_77_support_artifact_ids: tuple[str, ...]
    owner_role: str
    reviewer_role: str
    evidence_category: str
    evidence_status: str
    evidence_completeness_status: str
    evidence_sufficiency_status: str
    evidence_summary: str
    source_evidence_references: tuple[str, ...]
    required_follow_up_evidence_references: tuple[str, ...]
    unresolved_blocker_references: tuple[str, ...]
    unresolved_limitation_references: tuple[str, ...]
    non_authorization_confirmation: bool
    evidence_pack_limitation_notes: str
    severity: str
    safety_flags: tuple[str, ...]


@dataclass(frozen=True)
class EvidencePackFindingRecord:
    finding_id: str
    category: str
    related_item_id: str
    severity: str
    summary: str


@dataclass(frozen=True)
class EvidencePackLimitationRecord:
    limitation_id: str
    category: str
    related_item_id: str
    severity: str
    summary: str


@dataclass(frozen=True)
class XamanGovernanceClosureResponseResolutionEvidencePackSpec:
    phase: str
    objective: str
    evidence_pack_bundle_id: str
    source_closure_response_resolution_register_id: str
    source_closure_digest_response_bundle_id: str
    deterministic_timestamp: str
    evidence_pack_domains: tuple[str, ...]
    evidence_pack_records: tuple[EvidencePackRecord, ...]
    evidence_pack_findings: tuple[EvidencePackFindingRecord, ...]
    evidence_pack_limitation_register: tuple[EvidencePackLimitationRecord, ...]
    non_authorization_notices: tuple[str, ...]
    safety_flags: Phase88SafetyFlags = Phase88SafetyFlags()


@dataclass(frozen=True)
class XamanGovernanceClosureResponseResolutionEvidencePackFixtureInput:
    fixture_id: str
    evidence_pack_bundle_id: str
    source_closure_response_resolution_register_id: str
    source_closure_digest_response_bundle_id: str
    deterministic_timestamp: str
    closure_response_resolution_classification: str
    closure_digest_response_classification: str
    evidence_pack_records: tuple[EvidencePackRecord, ...]
    non_authorization_notices: tuple[str, ...]
    missing_evidence_pack: bool = False
    incomplete_evidence_pack: bool = False
    missing_required_evidence: bool = False
    stale_evidence_unresolved: bool = False
    redacted_evidence_unresolved: bool = False
    reference_only_evidence_unresolved: bool = False
    synthetic_only_evidence_unresolved: bool = False
    unverified_evidence_unresolved: bool = False
    missing_non_authorization_confirmation: bool = False
    missing_owner: bool = False
    missing_reviewer: bool = False
    missing_follow_up_evidence_reference: bool = False
    missing_evidence_sufficiency_mapping: bool = False
    unresolved_blocker_lacks_evidence: bool = False
    unresolved_limitation_lacks_evidence: bool = False
    dependency_audit_evidence_unresolved: bool = False
    safety_review_evidence_unresolved: bool = False
    superseded_evidence_missing_replacement: bool = False
    rejected_evidence_unresolved: bool = False
    traceability_gap: bool = False
    invalid_xaman_payload_approval_marker: bool = False
    invalid_wallet_material_approval_marker: bool = False
    invalid_signing_submission_autofill_approval_marker: bool = False
    invalid_testnet_live_execution_approval_marker: bool = False
    invalid_runtime_evidence_pack_service_marker: bool = False
    invalid_download_service_marker: bool = False
    invalid_api_ui_evidence_pack_route_marker: bool = False
    invalid_safety_bypass_marker: bool = False


@dataclass(frozen=True)
class XamanGovernanceClosureResponseResolutionEvidencePackReport:
    fixture_id: str
    spec: XamanGovernanceClosureResponseResolutionEvidencePackSpec
    final_evidence_pack_classification: str
    validation_errors: tuple[str, ...]
    blockers: tuple[str, ...]


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {key: jsonable(getattr(value, key)) for key in value.__dataclass_fields__}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    return value
