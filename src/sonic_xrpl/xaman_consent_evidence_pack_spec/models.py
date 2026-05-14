from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EVIDENCE_PACK_VALID = "EVIDENCE_PACK_VALID"
EVIDENCE_PACK_REVIEW_REQUIRED = "EVIDENCE_PACK_REVIEW_REQUIRED"
EVIDENCE_PACK_INVALID = "EVIDENCE_PACK_INVALID"
EVIDENCE_PACK_BLOCKED = "EVIDENCE_PACK_BLOCKED"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Phase67SafetyFlags:
    evidence_pack_spec_only: bool = True
    export_implementation_allowed: bool = False
    file_write_allowed: bool = False
    ui_implementation_allowed: bool = False
    api_route_allowed: bool = False
    runtime_service_allowed: bool = False
    persistence_implementation_allowed: bool = False
    database_writes_allowed: bool = False
    callback_handler_allowed: bool = False
    webhook_runtime_allowed: bool = False
    payload_creation_allowed: bool = False
    xaman_api_calls_allowed: bool = False
    signing_allowed: bool = False
    submission_allowed: bool = False
    wallet_material_allowed: bool = False
    testnet_execution_allowed: bool = False
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class EvidenceReferenceRequirement:
    key: str
    label: str
    required: bool
    rationale: str


@dataclass(frozen=True)
class Phase67Blocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_runtime_implementation: bool
    required_before_testnet_implementation: bool
    required_before_live_implementation: bool


@dataclass(frozen=True)
class XamanConsentEvidencePackSpec:
    phase: str
    objective: str
    evidence_pack_id: str
    candidate_id: str
    evidence_requirements: tuple[EvidenceReferenceRequirement, ...]
    traceability_requirements: tuple[str, ...]
    completeness_requirements: tuple[str, ...]
    blockers: tuple[Phase67Blocker, ...] = field(default_factory=tuple)
    safety_flags: Phase67SafetyFlags = Phase67SafetyFlags()


@dataclass(frozen=True)
class XamanConsentEvidencePackFixtureInput:
    fixture_id: str
    evidence_pack_id: str
    candidate_id: str
    has_candidate_identity: bool
    has_provenance: bool
    has_firstledger_intelligence_reference: bool
    has_paper_simulation_reference: bool
    has_paper_simulation_assumptions: bool
    has_xaman_payload_schema_reference: bool
    has_callback_verification_reference: bool
    has_audit_idempotency_reference: bool
    has_approval_state_machine_reference: bool
    has_consent_ux_reference: bool
    has_risk_disclosure_bundle: bool
    has_stale_missing_evidence_disclosure: bool
    has_no_live_execution_blocker: bool
    has_wallet_material_exclusion: bool
    has_secrets_exclusion: bool
    invalid_payload_created_marker: bool = False
    invalid_xaman_called_marker: bool = False
    invalid_signing_submission_marker: bool = False
    invalid_wallet_material_marker: bool = False
    invalid_export_file_write_marker: bool = False
    invalid_ui_api_runtime_marker: bool = False
    invalid_testnet_live_execution_marker: bool = False


@dataclass(frozen=True)
class XamanConsentEvidencePackSpecReport:
    fixture_id: str
    spec: XamanConsentEvidencePackSpec
    outcome: str
    validation_errors: tuple[str, ...]
    blocked_actions: tuple[str, ...]


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
