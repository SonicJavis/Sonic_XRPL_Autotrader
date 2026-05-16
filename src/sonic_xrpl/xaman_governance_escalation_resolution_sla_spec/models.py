from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SLA_NOT_READY = "NOT_READY"
SLA_REVIEW_REQUIRED = "REVIEW_REQUIRED"
SLA_SPEC_REVIEW_READY = "SPEC_REVIEW_READY"
SLA_OVERDUE = "OVERDUE"
SLA_BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Phase73SafetyFlags:
    spec_only: bool = True
    sla_spec_only: bool = True
    runtime_sla_engine_allowed: bool = False
    scheduler_allowed: bool = False
    notification_allowed: bool = False
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
class EscalationSLARecord:
    sla_id: str
    escalation_id: str
    workflow_step_id: str
    attestation_id: str
    signoff_domain: str
    governance_domain: str
    severity: str
    owner_role: str
    opened_at: str
    due_at: str
    due_policy: str
    required_resolution_evidence: str
    current_status: str
    overdue_classification: str
    expiry_classification: str
    blocker_severity_if_unresolved: str
    limitation_notes: str


@dataclass(frozen=True)
class ResolutionEvidenceRecord:
    resolution_evidence_id: str
    escalation_id: str
    evidence_artifact_id: str
    reviewer_role: str
    resolution_reason: str
    evidence_integrity_status: str
    attestation_linkage_status: str
    workflow_linkage_status: str
    accepted_for_spec_review: bool
    limitation_notes: str


@dataclass(frozen=True)
class XamanGovernanceEscalationResolutionSLASpec:
    phase: str
    objective: str
    sla_bundle_id: str
    sla_records: tuple[EscalationSLARecord, ...]
    resolution_evidence_records: tuple[ResolutionEvidenceRecord, ...]
    safety_flags: Phase73SafetyFlags = Phase73SafetyFlags()


@dataclass(frozen=True)
class XamanGovernanceEscalationResolutionSLAFixtureInput:
    fixture_id: str
    sla_bundle_id: str
    sla_records: tuple[EscalationSLARecord, ...]
    resolution_evidence_records: tuple[ResolutionEvidenceRecord, ...]
    has_dependency_audit_resolution: bool
    has_safety_scan_triage_resolution: bool
    invalid_payload_testnet_live_marker: bool = False
    invalid_wallet_material_ambiguity_marker: bool = False
    invalid_runtime_sla_scheduler_marker: bool = False
    invalid_runtime_notification_marker: bool = False


@dataclass(frozen=True)
class XamanGovernanceEscalationResolutionSLAReport:
    fixture_id: str
    spec: XamanGovernanceEscalationResolutionSLASpec
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
