from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ATTESTATION_NOT_READY = "NOT_READY"
ATTESTATION_REVIEW_REQUIRED = "REVIEW_REQUIRED"
ATTESTATION_SPEC_REVIEW_READY = "SPEC_REVIEW_READY"
ATTESTATION_BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Phase71SafetyFlags:
    spec_only: bool = True
    attestation_only: bool = True
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
class EvidenceArtifact:
    evidence_id: str
    source_path: str
    evidence_type: str
    governance_domain: str
    linked_signoff_domain: str
    deterministic_hash: str
    provenance_label: str
    synthetic_only: bool
    owner_role: str
    reviewed_at: str
    limitation_notes: str


@dataclass(frozen=True)
class AttestationRecord:
    attestation_id: str
    evidence_id: str
    reviewer_role: str
    attestation_status: str
    notes: str


@dataclass(frozen=True)
class IntegrityFinding:
    finding_id: str
    category: str
    severity: str
    detail: str


@dataclass(frozen=True)
class XamanGovernanceEvidenceAttestationSpec:
    phase: str
    objective: str
    bundle_id: str
    evidence_artifacts: tuple[EvidenceArtifact, ...]
    attestations: tuple[AttestationRecord, ...]
    findings: tuple[IntegrityFinding, ...] = field(default_factory=tuple)
    safety_flags: Phase71SafetyFlags = Phase71SafetyFlags()


@dataclass(frozen=True)
class XamanGovernanceEvidenceAttestationFixtureInput:
    fixture_id: str
    bundle_id: str
    evidence_artifacts: tuple[EvidenceArtifact, ...]
    attestations: tuple[AttestationRecord, ...]
    has_dependency_report: bool
    has_safety_scan_triage: bool
    has_rollback_evidence: bool
    has_incident_response_evidence: bool
    invalid_payload_or_execution_approval_marker: bool = False
    invalid_wallet_material_ambiguity_marker: bool = False


@dataclass(frozen=True)
class XamanGovernanceEvidenceAttestationReport:
    fixture_id: str
    spec: XamanGovernanceEvidenceAttestationSpec
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
