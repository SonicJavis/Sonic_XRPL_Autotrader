from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

READINESS_NOT_READY = "NOT_READY"
READINESS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
READINESS_SPEC_ONLY_READY = "SPEC_ONLY_READY"
READINESS_BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Phase70SafetyFlags:
    spec_only: bool = True
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
class GovernanceRequirement:
    key: str
    label: str
    owner_role: str
    mandatory_for_future_testnet_consideration: bool
    blocker_severity_if_missing: str
    spec_only: bool
    limitation_notes: str


@dataclass(frozen=True)
class GovernanceBlocker:
    blocker_id: str
    category: str
    severity: str
    title: str
    detail: str


@dataclass(frozen=True)
class XamanGovernanceSignoffMatrixSpec:
    phase: str
    objective: str
    matrix_id: str
    signoff_roles: tuple[str, ...]
    signoff_domains: tuple[str, ...]
    signoff_statuses: tuple[str, ...]
    evidence_requirements: tuple[GovernanceRequirement, ...]
    blockers: tuple[GovernanceBlocker, ...] = field(default_factory=tuple)
    safety_flags: Phase70SafetyFlags = Phase70SafetyFlags()


@dataclass(frozen=True)
class XamanGovernanceFixtureInput:
    fixture_id: str
    matrix_id: str
    has_safety_guards_evidence: bool
    has_xaman_payload_boundary_evidence: bool
    has_testnet_boundary_evidence: bool
    has_wallet_material_boundary_evidence: bool
    has_dependency_supply_chain_evidence: bool
    has_firstledger_data_boundary_evidence: bool
    has_operator_consent_evidence: bool
    has_rollback_readiness_evidence: bool
    has_observability_evidence: bool
    has_incident_response_evidence: bool
    has_legal_policy_review_evidence: bool
    has_safety_scan_review_triage: bool
    has_guard_critical_approval: bool
    invalid_xaman_payload_ambiguity_marker: bool = False
    invalid_wallet_material_ambiguity_marker: bool = False
    invalid_dependency_risk_marker: bool = False
    invalid_testnet_approved_marker: bool = False
    invalid_live_approved_marker: bool = False
    invalid_runtime_execution_marker: bool = False


@dataclass(frozen=True)
class XamanGovernanceSignoffReport:
    fixture_id: str
    spec: XamanGovernanceSignoffMatrixSpec
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
