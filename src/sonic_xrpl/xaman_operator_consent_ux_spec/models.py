from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CONSENT_SPEC_VALID = "CONSENT_SPEC_VALID"
CONSENT_SPEC_REVIEW_REQUIRED = "CONSENT_SPEC_REVIEW_REQUIRED"
CONSENT_SPEC_INVALID = "CONSENT_SPEC_INVALID"
CONSENT_BLOCKED = "CONSENT_BLOCKED"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Phase66SafetyFlags:
    ux_contract_spec_only: bool = True
    ui_implementation_allowed: bool = False
    api_route_allowed: bool = False
    runtime_consent_service_allowed: bool = False
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
class ConsentDisclosureRequirement:
    requirement_id: str
    label: str
    required: bool
    rationale: str


@dataclass(frozen=True)
class Phase66Blocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_ui_implementation: bool
    required_before_testnet_implementation: bool
    required_before_live_implementation: bool


@dataclass(frozen=True)
class XamanOperatorConsentUxSpec:
    phase: str
    objective: str
    candidate_id: str
    disclosures: tuple[ConsentDisclosureRequirement, ...]
    acknowledgement_requirements: tuple[str, ...]
    rejection_cancellation_requirements: tuple[str, ...]
    operator_audit_binding_requirements: tuple[str, ...]
    blockers: tuple[Phase66Blocker, ...] = field(default_factory=tuple)
    safety_flags: Phase66SafetyFlags = Phase66SafetyFlags()


@dataclass(frozen=True)
class XamanOperatorConsentUxFixtureInput:
    fixture_id: str
    candidate_id: str
    has_no_live_execution_disclosure: bool
    has_no_wallet_material_disclosure: bool
    has_payload_not_created_disclosure: bool
    has_signing_submission_unavailable_disclosure: bool
    has_risk_disclosure: bool
    has_source_provenance_section: bool
    has_paper_simulation_assumption_section: bool
    has_stale_missing_evidence_disclosure: bool
    has_operator_acknowledgement: bool
    has_confirmation_phrase_requirement: bool
    invalid_auto_approval_marker: bool = False
    invalid_one_click_execution_marker: bool = False
    attempted_ui_implementation_marker: bool = False
    attempted_api_route_marker: bool = False
    attempted_payload_creation_marker: bool = False
    attempted_xaman_api_marker: bool = False
    attempted_signing_submission_marker: bool = False
    attempted_wallet_material_marker: bool = False
    attempted_testnet_live_execution_marker: bool = False


@dataclass(frozen=True)
class XamanOperatorConsentUxSpecReport:
    fixture_id: str
    spec: XamanOperatorConsentUxSpec
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
