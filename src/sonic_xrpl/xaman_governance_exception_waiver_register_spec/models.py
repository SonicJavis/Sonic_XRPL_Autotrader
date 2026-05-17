from __future__ import annotations

from dataclasses import dataclass
from typing import Any

WAIVER_NOT_READY = "NOT_READY"
WAIVER_REVIEW_REQUIRED = "REVIEW_REQUIRED"
WAIVER_SPEC_REVIEW_READY = "SPEC_REVIEW_READY"
WAIVER_EXPIRED = "EXPIRED"
WAIVER_REVOKED = "REVOKED"
WAIVER_BLOCKED = "BLOCKED"

WAIVER_ROLES = (
    "WAIVER_REQUESTER",
    "SECURITY_WAIVER_REVIEWER",
    "XRPL_PROTOCOL_WAIVER_REVIEWER",
    "XAMAN_WAIVER_REVIEWER",
    "SUPPLY_CHAIN_WAIVER_REVIEWER",
    "RISK_WAIVER_REVIEWER",
    "AUDIT_WAIVER_REVIEWER",
    "FINAL_GOVERNANCE_OWNER",
)

WAIVER_DOMAINS = (
    "SAFETY_GUARD_WAIVER",
    "EVIDENCE_INTEGRITY_WAIVER",
    "ATTESTATION_WAIVER",
    "SIGNOFF_MATRIX_WAIVER",
    "REVIEW_WORKFLOW_WAIVER",
    "ESCALATION_SLA_WAIVER",
    "DEPENDENCY_RISK_WAIVER",
    "XAMAN_BOUNDARY_WAIVER",
    "WALLET_MATERIAL_WAIVER",
    "TESTNET_BOUNDARY_WAIVER",
    "LIVE_BOUNDARY_WAIVER",
    "ROLLBACK_READINESS_WAIVER",
    "INCIDENT_RESPONSE_WAIVER",
    "DOCS_DRIFT_WAIVER",
)

WAIVER_SEVERITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL", "BLOCKING")
WAIVER_STATUSES = (
    "REQUESTED",
    "EVIDENCE_PENDING",
    "IN_REVIEW",
    "ACCEPTED_FOR_SPEC_REVIEW",
    "REJECTED",
    "REVOKED",
    "EXPIRED",
    "SUPERSEDED",
    "BLOCKED",
)

EXPIRY_REVOCATION_RULES = (
    "waivers_cannot_be_indefinite_unless_docs_only_spec_only",
    "critical_and_blocking_waivers_require_expiry",
    "wallet_material_ambiguity_waivers_are_blocked",
    "xaman_payload_ambiguity_waivers_are_blocked",
    "testnet_or_live_execution_waivers_are_blocked",
    "signing_submission_autofill_waivers_are_blocked",
    "runtime_mutation_waivers_are_blocked",
    "missing_evidence_cannot_be_waived_for_execution_readiness",
    "stale_evidence_requires_review_or_expiry",
    "dependency_audit_waivers_require_explicit_risk_classification",
    "revoked_waivers_cannot_become_accepted",
    "expired_waivers_require_renewed_evidence_before_acceptance",
    "superseded_waivers_require_replacement_waiver_id",
    "accepted_for_spec_review_never_implies_execution_readiness",
)

BLOCKER_CATEGORIES = (
    "UNSAFE_WAIVER_TARGET",
    "MISSING_WAIVER_EVIDENCE",
    "STALE_WAIVER_EVIDENCE",
    "MISSING_REVIEWER",
    "MISSING_EXPIRY_POLICY",
    "MISSING_REVOCATION_POLICY",
    "MISSING_COMPENSATING_CONTROL",
    "DEPENDENCY_AUDIT_WAIVER_RISK",
    "UNTRIAGED_SAFETY_REVIEW_WAIVER_RISK",
    "XAMAN_PAYLOAD_WAIVER_ATTEMPT",
    "WALLET_MATERIAL_WAIVER_ATTEMPT",
    "TESTNET_LIVE_EXECUTION_WAIVER_ATTEMPT",
    "SIGNING_SUBMISSION_AUTOFILL_WAIVER_ATTEMPT",
    "RUNTIME_MUTATION_WAIVER_ATTEMPT",
    "GUARD_WEAKENING_WAIVER_ATTEMPT",
    "SAFETY_BYPASS_MARKER",
)

@dataclass(frozen=True)
class Phase74SafetyFlags:
    spec_only: bool = True
    waiver_register_spec_only: bool = True
    runtime_waiver_service_allowed: bool = False
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
class WaiverRequestRecord:
    waiver_id: str
    waiver_domain: str
    severity: str
    requester_role: str
    reviewer_role: str
    related_phase70_signoff_domain: str
    related_phase71_attestation_id: str
    related_phase72_workflow_step_id: str
    related_phase73_sla_escalation_id: str
    requested_exception_summary: str
    required_evidence_ids: tuple[str, ...]
    supplied_evidence_ids: tuple[str, ...]
    stale_evidence_ids: tuple[str, ...]
    risk_acceptance_rationale: str
    compensating_control_references: tuple[str, ...]
    expiry_policy: str
    revocation_policy: str
    current_status: str
    limitation_notes: str
    docs_only_spec_only: bool
    replacement_waiver_id: str
    safety_flags: tuple[str, ...]
    dependency_risk_classification: str

@dataclass(frozen=True)
class XamanGovernanceExceptionWaiverRegisterSpec:
    phase: str
    objective: str
    waiver_register_id: str
    deterministic_timestamp: str
    waiver_roles: tuple[str, ...]
    waiver_domains: tuple[str, ...]
    waiver_severities: tuple[str, ...]
    waiver_statuses: tuple[str, ...]
    expiry_revocation_rules: tuple[str, ...]
    blocker_categories: tuple[str, ...]
    waiver_records: tuple[WaiverRequestRecord, ...]
    limitations: tuple[str, ...]
    safety_flags: Phase74SafetyFlags = Phase74SafetyFlags()

@dataclass(frozen=True)
class XamanGovernanceExceptionWaiverRegisterFixtureInput:
    fixture_id: str
    waiver_register_id: str
    deterministic_timestamp: str
    waiver_records: tuple[WaiverRequestRecord, ...]
    has_dependency_audit_resolution: bool
    has_safety_scan_triage_resolution: bool
    invalid_xaman_payload_waiver_marker: bool = False
    invalid_wallet_material_waiver_marker: bool = False
    invalid_signing_submission_autofill_waiver_marker: bool = False
    invalid_testnet_live_execution_waiver_marker: bool = False
    invalid_runtime_mutation_waiver_marker: bool = False
    invalid_guard_weakening_waiver_marker: bool = False
    invalid_safety_bypass_marker: bool = False

@dataclass(frozen=True)
class XamanGovernanceExceptionWaiverRegisterReport:
    fixture_id: str
    spec: XamanGovernanceExceptionWaiverRegisterSpec
    readiness_classification: str
    validation_errors: tuple[str, ...]
    blockers: tuple[str, ...]


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {k: jsonable(getattr(value, k)) for k in value.__dataclass_fields__}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return value
