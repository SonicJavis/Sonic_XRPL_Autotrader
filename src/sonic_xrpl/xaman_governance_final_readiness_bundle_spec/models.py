from __future__ import annotations

from dataclasses import dataclass
from typing import Any

FINAL_NOT_READY = "NOT_READY"
FINAL_REVIEW_REQUIRED = "REVIEW_REQUIRED"
FINAL_SPEC_REVIEW_READY = "SPEC_REVIEW_READY"
FINAL_BLOCKED = "BLOCKED"
FINAL_INCOMPLETE = "INCOMPLETE"

FINAL_BUNDLE_DOMAINS = (
    "SIGNOFF_MATRIX",
    "EVIDENCE_ATTESTATION",
    "REVIEW_WORKFLOW",
    "ESCALATION_SLA",
    "EXCEPTION_WAIVER_REGISTER",
    "SAFETY_GUARDS",
    "DEPENDENCY_AUDIT",
    "RUNTIME_PROFILE",
    "LIVE_READINESS_POLICY",
    "XAMAN_BOUNDARY_POLICY",
    "ROLLBACK_READINESS",
    "INCIDENT_RESPONSE",
    "DOCS_CONSISTENCY",
)

MANDATORY_ARTIFACT_TYPES = (
    "PHASE70_SIGNOFF_MATRIX_REPORT",
    "PHASE71_ATTESTATION_BUNDLE_REPORT",
    "PHASE72_REVIEW_WORKFLOW_REPORT",
    "PHASE73_SLA_BUNDLE_REPORT",
    "PHASE74_WAIVER_REGISTER_REPORT",
    "SAFETY_SCAN_SUMMARY",
    "DEPENDENCY_AUDIT_SUMMARY",
    "RUNTIME_PROFILE_CONFORMANCE_SUMMARY",
    "LIVE_READINESS_POLICY_REFERENCE",
    "XAMAN_BOUNDARY_POLICY_REFERENCE",
    "ROLLBACK_READINESS_REFERENCE",
    "INCIDENT_RESPONSE_REFERENCE",
)

COMPLETENESS_CHECKS = (
    "phase70_report_present",
    "phase71_report_present",
    "phase72_report_present",
    "phase73_report_present",
    "phase74_report_present",
    "all_mandatory_domains_represented",
    "no_missing_required_artifact",
    "no_revoked_waiver_accepted",
    "no_expired_waiver_accepted",
    "no_overdue_critical_sla_unresolved",
    "no_blocker_hidden_by_waiver",
    "no_untriaged_safety_review_relied_upon_as_approval",
    "dependency_audit_present",
    "no_payload_api_sdk_approval_wording",
    "no_signing_submission_autofill_wallet_approval_wording",
    "no_testnet_live_execution_approval_wording",
    "no_runtime_service_approval_wording",
    "all_outputs_spec_only",
)

LIMITATION_CATEGORIES = (
    "MISSING_REQUIRED_ARTIFACT",
    "STALE_ARTIFACT",
    "UNVERIFIABLE_ARTIFACT_HASH",
    "UNRESOLVED_SAFETY_REVIEW",
    "UNRESOLVED_DEPENDENCY_AUDIT_RISK",
    "EXPIRED_WAIVER",
    "REVOKED_WAIVER",
    "UNSAFE_WAIVER_ATTEMPT",
    "OVERDUE_CRITICAL_SLA",
    "AMBIGUOUS_SIGNOFF_LINKAGE",
    "MISSING_ROLLBACK_EVIDENCE",
    "MISSING_INCIDENT_RESPONSE_EVIDENCE",
    "XAMAN_PAYLOAD_AMBIGUITY",
    "WALLET_MATERIAL_AMBIGUITY",
    "TESTNET_LIVE_APPROVAL_AMBIGUITY",
    "RUNTIME_SERVICE_AMBIGUITY",
    "DOCS_DRIFT",
)

@dataclass(frozen=True)
class Phase75SafetyFlags:
    spec_only: bool = True
    final_readiness_bundle_spec_only: bool = True
    runtime_readiness_service_allowed: bool = False
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
class BundleArtifactReference:
    artifact_id: str
    phase_number: str
    artifact_type: str
    source_path: str
    declared_hash: str
    required_classification: str
    artifact_status: str
    limitation_notes: str
    safety_flags: tuple[str, ...]

@dataclass(frozen=True)
class LimitationRecord:
    limitation_id: str
    category: str
    related_artifact_id: str
    severity: str
    summary: str

@dataclass(frozen=True)
class XamanGovernanceFinalReadinessBundleSpec:
    phase: str
    objective: str
    final_bundle_id: str
    deterministic_timestamp: str
    final_bundle_domains: tuple[str, ...]
    artifact_references: tuple[BundleArtifactReference, ...]
    completeness_checks: tuple[str, ...]
    limitation_register: tuple[LimitationRecord, ...]
    safety_flags: Phase75SafetyFlags = Phase75SafetyFlags()

@dataclass(frozen=True)
class XamanGovernanceFinalReadinessBundleFixtureInput:
    fixture_id: str
    final_bundle_id: str
    deterministic_timestamp: str
    artifact_references: tuple[BundleArtifactReference, ...]
    phase70_present: bool
    phase71_present: bool
    phase72_present: bool
    phase73_present: bool
    phase74_present: bool
    unresolved_safety_review: bool
    unresolved_dependency_risk: bool
    expired_waiver: bool
    revoked_waiver: bool
    overdue_critical_sla: bool
    unsafe_waiver_attempt: bool
    ambiguous_signoff_linkage: bool
    missing_rollback_evidence: bool
    missing_incident_response_evidence: bool
    invalid_xaman_payload_approval_marker: bool = False
    invalid_wallet_material_approval_marker: bool = False
    invalid_signing_submission_autofill_approval_marker: bool = False
    invalid_testnet_live_execution_approval_marker: bool = False
    invalid_runtime_readiness_service_marker: bool = False
    invalid_safety_bypass_marker: bool = False

@dataclass(frozen=True)
class XamanGovernanceFinalReadinessBundleReport:
    fixture_id: str
    spec: XamanGovernanceFinalReadinessBundleSpec
    final_readiness_classification: str
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
