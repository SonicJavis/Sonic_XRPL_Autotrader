from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EXPORT_NOT_READY = "EXPORT_NOT_READY"
EXPORT_REVIEW_REQUIRED = "EXPORT_REVIEW_REQUIRED"
EXPORT_SPEC_REVIEW_READY = "EXPORT_SPEC_REVIEW_READY"
EXPORT_BLOCKED = "EXPORT_BLOCKED"
EXPORT_INCOMPLETE = "EXPORT_INCOMPLETE"

EXPORT_DOMAINS = (
    "FINAL_READINESS_BUNDLE", "SIGNOFF_MATRIX", "EVIDENCE_ATTESTATION", "REVIEW_WORKFLOW",
    "ESCALATION_SLA", "EXCEPTION_WAIVER_REGISTER", "SAFETY_GUARDS", "DEPENDENCY_AUDIT",
    "RUNTIME_PROFILE", "POLICY_DOCS", "ROLLBACK_READINESS", "INCIDENT_RESPONSE",
    "LIMITATION_REGISTER", "TRACEABILITY_MAP",
)
MANDATORY_ARTIFACT_TYPES = (
    "PHASE75_FINAL_READINESS_BUNDLE_REPORT", "PHASE70_SIGNOFF_MATRIX_REPORT", "PHASE71_ATTESTATION_BUNDLE_REPORT",
    "PHASE72_REVIEW_WORKFLOW_REPORT", "PHASE73_SLA_BUNDLE_REPORT", "PHASE74_WAIVER_REGISTER_REPORT",
)
INCLUSION_STATUSES = ("INCLUDED", "REFERENCE_ONLY", "REDACTED", "EXCLUDED", "MISSING", "BLOCKED")
REDACTION_LABELS = (
    "NO_REDACTION_REQUIRED", "REDACTED_SYNTHETIC_FIXTURE", "REDACTED_SECURITY_DETAIL",
    "REFERENCE_ONLY_POLICY", "BLOCKED_UNSAFE_CONTENT", "MISSING_REQUIRED_ARTIFACT",
)
LIMITATION_CATEGORIES = (
    "MISSING_REQUIRED_ARTIFACT", "STALE_ARTIFACT", "UNVERIFIABLE_ARTIFACT_HASH", "REDACTED_ARTIFACT_REQUIRES_REVIEW",
    "REFERENCE_ONLY_ARTIFACT_REQUIRES_MANUAL_VERIFICATION", "UNRESOLVED_SAFETY_REVIEW", "UNRESOLVED_DEPENDENCY_AUDIT_RISK",
    "EXPIRED_WAIVER", "REVOKED_WAIVER", "UNSAFE_WAIVER_ATTEMPT", "OVERDUE_CRITICAL_SLA", "AMBIGUOUS_SIGNOFF_LINKAGE",
    "MISSING_ROLLBACK_EVIDENCE", "MISSING_INCIDENT_RESPONSE_EVIDENCE", "XAMAN_PAYLOAD_AMBIGUITY", "WALLET_MATERIAL_AMBIGUITY",
    "TESTNET_LIVE_APPROVAL_AMBIGUITY", "RUNTIME_EXPORT_SERVICE_AMBIGUITY", "DOCS_DRIFT",
)

@dataclass(frozen=True)
class Phase76SafetyFlags:
    spec_only: bool = True
    review_export_spec_only: bool = True
    runtime_export_service_allowed: bool = False
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
class ExportArtifactRecord:
    export_artifact_id: str
    source_phase_number: str
    source_artifact_type: str
    source_reference: str
    declared_hash: str
    inclusion_status: str
    redaction_status: str
    reviewer_visibility: str
    required_classification: str
    limitation_notes: str
    safety_flags: tuple[str, ...]

@dataclass(frozen=True)
class ExportLimitationRecord:
    limitation_id: str
    category: str
    related_artifact_id: str
    severity: str
    summary: str

@dataclass(frozen=True)
class ReviewerSummary:
    summary_type: str
    text: str
    related_artifact_ids: tuple[str, ...]

@dataclass(frozen=True)
class ExportManifest:
    manifest_id: str
    package_id: str
    phase_number: str
    deterministic_timestamp: str
    artifact_ids: tuple[str, ...]
    artifact_hashes: tuple[str, ...]
    redaction_labels: tuple[str, ...]
    reviewer_summary_types: tuple[str, ...]
    cross_phase_traceability_refs: tuple[str, ...]
    limitation_ids: tuple[str, ...]
    blockers: tuple[str, ...]

@dataclass(frozen=True)
class XamanGovernanceFinalReadinessReviewExportSpec:
    phase: str
    objective: str
    export_package_id: str
    deterministic_timestamp: str
    export_domains: tuple[str, ...]
    export_artifacts: tuple[ExportArtifactRecord, ...]
    reviewer_summaries: tuple[ReviewerSummary, ...]
    limitation_register: tuple[ExportLimitationRecord, ...]
    manifest: ExportManifest
    safety_flags: Phase76SafetyFlags = Phase76SafetyFlags()

@dataclass(frozen=True)
class XamanGovernanceFinalReadinessReviewExportFixtureInput:
    fixture_id: str
    export_package_id: str
    manifest_id: str
    deterministic_timestamp: str
    export_artifacts: tuple[ExportArtifactRecord, ...]
    phase75_present: bool
    phase70_present: bool
    phase71_present: bool
    phase72_present: bool
    phase73_present: bool
    phase74_present: bool
    unresolved_blocker_summary: bool
    unresolved_limitation_summary: bool
    expired_waiver_included: bool
    revoked_waiver_included: bool
    overdue_critical_sla_included: bool
    unsafe_waiver_attempt_included: bool
    invalid_xaman_payload_approval_marker: bool = False
    invalid_wallet_material_approval_marker: bool = False
    invalid_signing_submission_autofill_approval_marker: bool = False
    invalid_testnet_live_execution_approval_marker: bool = False
    invalid_runtime_export_service_marker: bool = False
    invalid_download_service_marker: bool = False
    invalid_api_ui_export_route_marker: bool = False
    invalid_safety_bypass_marker: bool = False

@dataclass(frozen=True)
class XamanGovernanceFinalReadinessReviewExportReport:
    fixture_id: str
    spec: XamanGovernanceFinalReadinessReviewExportSpec
    export_readiness_classification: str
    validation_errors: tuple[str, ...]
    blockers: tuple[str, ...]

def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {k: jsonable(getattr(value, k)) for k in value.__dataclass_fields__}
    if isinstance(value, tuple):
        return [jsonable(v) for v in value]
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return value
