from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Phase63SafetyFlags:
    callback_spec_only: bool = True
    verification_design_only: bool = True
    manual_approval_required: bool = True
    runtime_callback_handler_allowed: bool = False
    webhook_runtime_allowed: bool = False
    payload_creation_allowed: bool = False
    xaman_api_calls_allowed: bool = False
    signing_allowed: bool = False
    submission_allowed: bool = False
    autofill_allowed: bool = False
    wallet_material_allowed: bool = False
    testnet_execution_allowed: bool = False
    live_execution_allowed: bool = False
    runtime_mutation_allowed: bool = False


@dataclass(frozen=True)
class CallbackFieldRequirements:
    required_fields: tuple[str, ...]
    prohibited_fields: tuple[str, ...]
    correlation_id_required: bool
    payload_uuid_binding_required: bool
    candidate_binding_required: bool
    paper_simulation_binding_required: bool
    operator_consent_linkage_required: bool


@dataclass(frozen=True)
class ReplayAndIdempotencyRequirements:
    nonce_required: bool
    ttl_required: bool
    ttl_min_seconds: int
    ttl_max_seconds: int
    replay_window_seconds: int
    idempotency_key_required: bool
    duplicate_callback_handling_required: bool
    callback_ordering_required: bool


@dataclass(frozen=True)
class AuditAndGateRequirements:
    authenticity_checklist_required: bool
    audit_trail_required: bool
    cancellation_and_rejection_handling_required: bool
    testnet_gate_checklist_required: bool
    live_readiness_blockers_required: bool


@dataclass(frozen=True)
class Phase63Blocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_callback_runtime: bool
    required_before_testnet_impl: bool
    required_before_mainnet_impl: bool


@dataclass(frozen=True)
class XamanCallbackVerificationSpec:
    phase: str
    objective: str
    candidate_id: str
    callback_fields: CallbackFieldRequirements
    replay_and_idempotency: ReplayAndIdempotencyRequirements
    audit_and_gates: AuditAndGateRequirements
    blockers: tuple[Phase63Blocker, ...] = field(default_factory=tuple)
    safety_flags: Phase63SafetyFlags = Phase63SafetyFlags()


@dataclass(frozen=True)
class XamanCallbackFixtureInput:
    fixture_id: str
    candidate_id: str
    authenticity_requirement_present: bool
    required_fields_present: bool
    prohibited_fields_declared: bool
    correlation_id_present: bool
    payload_uuid_binding_present: bool
    candidate_binding_present: bool
    paper_simulation_binding_present: bool
    nonce_requirement_present: bool
    ttl_requirement_present: bool
    ttl_seconds: int | None
    replay_window_seconds: int | None
    idempotency_requirement_present: bool
    duplicate_callback_handling_present: bool
    callback_ordering_requirement_present: bool
    audit_trail_requirement_present: bool
    cancellation_and_rejection_requirement_present: bool
    operator_consent_linkage_present: bool
    testnet_gate_complete: bool
    live_gate_blocked: bool
    attempted_callback_handler: bool = False
    attempted_webhook_runtime: bool = False
    attempted_xaman_api_call: bool = False
    attempted_payload_creation: bool = False
    attempted_signing: bool = False
    attempted_submission: bool = False
    attempted_wallet_material: bool = False
    attempted_testnet_execution: bool = False
    attempted_live_execution: bool = False


@dataclass(frozen=True)
class XamanCallbackVerificationSpecReport:
    fixture_id: str
    spec: XamanCallbackVerificationSpec
    valid_design_spec: bool
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
