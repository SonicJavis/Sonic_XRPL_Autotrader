from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SPEC_ACCEPTED = "SPEC_ACCEPTED"
SPEC_REVIEW_REQUIRED = "SPEC_REVIEW_REQUIRED"
SPEC_REJECTED = "SPEC_REJECTED"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Phase64SafetyFlags:
    audit_spec_only: bool = True
    idempotency_spec_only: bool = True
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
class AuditEnvelopeSpec:
    event_type_enum_required: bool
    correlation_id_required: bool
    callback_event_id_required: bool
    payload_uuid_binding_required: bool
    candidate_binding_required: bool
    paper_simulation_binding_required: bool
    operator_approval_binding_required: bool
    risk_disclosure_linkage_required: bool


@dataclass(frozen=True)
class IdempotencySpec:
    idempotency_key_required: bool
    key_derivation_rule_required: bool
    conflict_policy_required: bool
    duplicate_callback_policy_required: bool
    replay_attempt_policy_required: bool
    stale_callback_policy_required: bool
    ttl_seconds_required: bool
    ttl_min_seconds: int
    ttl_max_seconds: int


@dataclass(frozen=True)
class AuditTrailSpec:
    append_only_required: bool
    tamper_evidence_required: bool
    retention_policy_required: bool
    redaction_policy_required: bool
    sensitive_material_exclusion_required: bool
    cancellation_rejection_policy_required: bool


@dataclass(frozen=True)
class Phase64Blocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_persistence_implementation: bool
    required_before_testnet_implementation: bool
    required_before_live_implementation: bool


@dataclass(frozen=True)
class XamanAuditIdempotencySpec:
    phase: str
    objective: str
    candidate_id: str
    audit_envelope: AuditEnvelopeSpec
    idempotency: IdempotencySpec
    audit_trail: AuditTrailSpec
    blockers: tuple[Phase64Blocker, ...] = field(default_factory=tuple)
    safety_flags: Phase64SafetyFlags = Phase64SafetyFlags()


@dataclass(frozen=True)
class XamanAuditIdempotencyFixtureInput:
    fixture_id: str
    candidate_id: str
    correlation_id_present: bool
    callback_event_id_present: bool
    payload_uuid_binding_present: bool
    candidate_binding_present: bool
    paper_simulation_binding_present: bool
    operator_approval_binding_present: bool
    risk_disclosure_linkage_present: bool
    idempotency_key_rule_present: bool
    idempotency_conflict_policy_present: bool
    duplicate_callback_policy_present: bool
    replay_policy_present: bool
    stale_callback_policy_present: bool
    ttl_seconds: int | None
    append_only_required_present: bool
    tamper_evidence_required_present: bool
    retention_policy_present: bool
    redaction_policy_present: bool
    sensitive_material_exclusion_present: bool
    cancellation_rejection_policy_present: bool
    testnet_gate_complete: bool
    live_gate_blocked: bool
    attempted_database_write: bool = False
    attempted_persistence_implementation: bool = False
    attempted_callback_handler: bool = False
    attempted_xaman_api_call: bool = False
    attempted_payload_creation: bool = False
    attempted_signing: bool = False
    attempted_submission: bool = False
    attempted_wallet_material: bool = False
    attempted_testnet_execution: bool = False
    attempted_live_execution: bool = False


@dataclass(frozen=True)
class XamanAuditIdempotencySpecReport:
    fixture_id: str
    spec: XamanAuditIdempotencySpec
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
