from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVIDENCE_PACK_DIGEST_NOT_READY = "EVIDENCE_PACK_DIGEST_NOT_READY"
EVIDENCE_PACK_DIGEST_REVIEW_REQUIRED = "EVIDENCE_PACK_DIGEST_REVIEW_REQUIRED"
EVIDENCE_PACK_DIGEST_SPEC_REVIEW_READY = "EVIDENCE_PACK_DIGEST_SPEC_REVIEW_READY"
EVIDENCE_PACK_DIGEST_BLOCKED = "EVIDENCE_PACK_DIGEST_BLOCKED"
EVIDENCE_PACK_DIGEST_INCOMPLETE = "EVIDENCE_PACK_DIGEST_INCOMPLETE"

REVIEW_DIGEST_DOMAINS = (
    "CLOSURE_RESPONSE_RESOLUTION_EVIDENCE_PACK",
    "EVIDENCE_PACK_RECORDS",
    "EVIDENCE_COMPLETENESS",
    "EVIDENCE_SUFFICIENCY",
    "FOLLOW_UP_EVIDENCE",
    "UNRESOLVED_BLOCKERS",
    "UNRESOLVED_LIMITATIONS",
    "NON_AUTHORIZATION_CONFIRMATIONS",
    "OWNER_REVIEWER_MAPPING",
    "DEPENDENCY_AUDIT",
    "SAFETY_REVIEW",
    "CLOSURE_RESPONSE_RESOLUTION_REGISTER",
    "CLOSURE_DIGEST_RESPONSE",
    "CLOSURE_REVIEW_DIGEST",
    "RESOLUTION_EVIDENCE_CLOSURE",
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
    "no runtime evidence-pack review digest service authorized",
    "no download/API/UI route authorized",
    "no safety bypass authorized",
)


@dataclass(frozen=True)
class Phase89SafetyFlags:
    spec_only: bool = True
    closure_response_evidence_pack_review_digest_spec_only: bool = True
    runtime_evidence_pack_review_digest_service_allowed: bool = False
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
class ReviewDigestSectionRecord:
    digest_section_id: str
    digest_domain: str
    related_phase88_evidence_pack_id: str
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
    section_title: str
    section_summary: str
    evidence_count: int
    complete_evidence_count: int
    incomplete_evidence_count: int
    sufficient_evidence_count: int
    insufficient_evidence_count: int
    blocker_count: int
    limitation_count: int
    reviewer_visibility: str
    digest_status: str
    severity: str
    limitation_notes: str
    safety_flags: tuple[str, ...]


@dataclass(frozen=True)
class ReviewDigestFindingRecord:
    finding_id: str
    category: str
    related_item_id: str
    severity: str
    summary: str


@dataclass(frozen=True)
class ReviewDigestLimitationRecord:
    limitation_id: str
    category: str
    related_item_id: str
    severity: str
    summary: str


@dataclass(frozen=True)
class XamanGovernanceClosureResponseEvidencePackReviewDigestSpec:
    phase: str
    objective: str
    review_digest_bundle_id: str
    source_phase88_evidence_pack_bundle_id: str
    source_closure_response_resolution_register_id: str
    deterministic_timestamp: str
    review_digest_domains: tuple[str, ...]
    review_digest_sections: tuple[ReviewDigestSectionRecord, ...]
    review_digest_findings: tuple[ReviewDigestFindingRecord, ...]
    review_digest_limitation_register: tuple[ReviewDigestLimitationRecord, ...]
    non_authorization_notices: tuple[str, ...]
    safety_flags: Phase89SafetyFlags = Phase89SafetyFlags()


@dataclass(frozen=True)
class XamanGovernanceClosureResponseEvidencePackReviewDigestFixtureInput:
    fixture_id: str
    review_digest_bundle_id: str
    source_phase88_evidence_pack_bundle_id: str
    source_closure_response_resolution_register_id: str
    deterministic_timestamp: str
    evidence_pack_classification: str
    closure_response_resolution_classification: str
    review_digest_sections: tuple[ReviewDigestSectionRecord, ...]
    non_authorization_notices: tuple[str, ...]
    missing_evidence_pack: bool = False
    incomplete_evidence_pack: bool = False
    blocked_evidence_pack: bool = False
    missing_evidence_completeness_summary: bool = False
    missing_evidence_sufficiency_summary: bool = False
    missing_owner_reviewer_summary: bool = False
    missing_non_authorization_summary: bool = False
    hidden_unresolved_blocker: bool = False
    hidden_unresolved_limitation: bool = False
    stale_evidence_summary_gap: bool = False
    redacted_evidence_summary_gap: bool = False
    reference_only_evidence_summary_gap: bool = False
    synthetic_only_evidence_summary_gap: bool = False
    unverified_evidence_summary_gap: bool = False
    dependency_audit_evidence_summary_gap: bool = False
    safety_review_evidence_summary_gap: bool = False
    rejected_evidence_unresolved: bool = False
    superseded_evidence_missing_replacement: bool = False
    traceability_gap: bool = False
    invalid_xaman_payload_approval_marker: bool = False
    invalid_wallet_material_approval_marker: bool = False
    invalid_signing_submission_autofill_approval_marker: bool = False
    invalid_testnet_live_execution_approval_marker: bool = False
    invalid_runtime_review_digest_service_marker: bool = False
    invalid_download_service_marker: bool = False
    invalid_api_ui_evidence_pack_digest_route_marker: bool = False
    invalid_safety_bypass_marker: bool = False


@dataclass(frozen=True)
class XamanGovernanceClosureResponseEvidencePackReviewDigestReport:
    fixture_id: str
    spec: XamanGovernanceClosureResponseEvidencePackReviewDigestSpec
    final_review_digest_classification: str
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
