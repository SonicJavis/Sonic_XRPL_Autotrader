from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

WORKFLOW_NOT_READY = "NOT_READY"
WORKFLOW_REVIEW_REQUIRED = "REVIEW_REQUIRED"
WORKFLOW_SPEC_REVIEW_READY = "SPEC_REVIEW_READY"
WORKFLOW_BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Phase72SafetyFlags:
    spec_only: bool = True
    workflow_spec_only: bool = True
    runtime_workflow_allowed: bool = False
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
class WorkflowStep:
    step_id: str
    stage_type: str
    role: str
    status: str
    linked_evidence_id: str
    linked_attestation_id: str
    notes: str


@dataclass(frozen=True)
class WorkflowTransition:
    source_status: str
    target_status: str
    allowed: bool
    rationale: str


@dataclass(frozen=True)
class EvidenceHandoff:
    handoff_id: str
    from_role: str
    to_role: str
    evidence_id: str
    attestation_id: str
    governance_domain: str
    handoff_reason: str
    required_action: str
    blocker_severity_if_unresolved: str
    limitation_notes: str


@dataclass(frozen=True)
class EscalationRecord:
    escalation_id: str
    source_step_id: str
    escalation_reason: str
    severity: str
    escalation_owner: str
    required_resolution_evidence: str
    resolution_status: str
    limitation_notes: str


@dataclass(frozen=True)
class XamanGovernanceEvidenceReviewWorkflowSpec:
    phase: str
    objective: str
    workflow_id: str
    steps: tuple[WorkflowStep, ...]
    transitions: tuple[WorkflowTransition, ...]
    handoffs: tuple[EvidenceHandoff, ...]
    escalations: tuple[EscalationRecord, ...] = field(default_factory=tuple)
    safety_flags: Phase72SafetyFlags = Phase72SafetyFlags()


@dataclass(frozen=True)
class XamanGovernanceEvidenceReviewWorkflowFixtureInput:
    fixture_id: str
    workflow_id: str
    steps: tuple[WorkflowStep, ...]
    handoffs: tuple[EvidenceHandoff, ...]
    escalations: tuple[EscalationRecord, ...]
    has_evidence_intake: bool
    has_dependency_report: bool
    has_safety_scan_triage: bool
    has_rollback_evidence: bool
    has_incident_response_evidence: bool
    invalid_payload_testnet_live_marker: bool = False
    invalid_wallet_material_ambiguity_marker: bool = False
    invalid_runtime_workflow_marker: bool = False


@dataclass(frozen=True)
class XamanGovernanceEvidenceReviewWorkflowReport:
    fixture_id: str
    spec: XamanGovernanceEvidenceReviewWorkflowSpec
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
