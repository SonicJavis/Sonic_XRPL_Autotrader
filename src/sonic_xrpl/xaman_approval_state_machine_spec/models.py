from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SPEC_VALID = "SPEC_VALID"
SPEC_REVIEW_REQUIRED = "SPEC_REVIEW_REQUIRED"
SPEC_INVALID = "SPEC_INVALID"
TRANSITION_BLOCKED = "TRANSITION_BLOCKED"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Phase65SafetyFlags:
    state_machine_spec_only: bool = True
    runtime_state_machine_allowed: bool = False
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
class TransitionRequirement:
    source_state: str
    target_state: str
    required_evidence: tuple[str, ...]
    required_audit_entry: bool
    idempotency_required: bool
    replay_ttl_required: bool
    human_approval_required: bool
    forbidden_runtime_behavior_note: str


@dataclass(frozen=True)
class InvalidTransitionRule:
    source_state: str
    target_state: str
    reason: str


@dataclass(frozen=True)
class Phase65Blocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_runtime_implementation: bool
    required_before_testnet_implementation: bool
    required_before_live_implementation: bool


@dataclass(frozen=True)
class XamanApprovalStateMachineSpec:
    phase: str
    objective: str
    candidate_id: str
    allowed_states: tuple[str, ...]
    transition_requirements: tuple[TransitionRequirement, ...]
    invalid_transition_rules: tuple[InvalidTransitionRule, ...]
    blockers: tuple[Phase65Blocker, ...] = field(default_factory=tuple)
    safety_flags: Phase65SafetyFlags = Phase65SafetyFlags()


@dataclass(frozen=True)
class XamanApprovalStateMachineFixtureInput:
    fixture_id: str
    candidate_id: str
    has_operator_approval_transition: bool
    has_callback_verification_transition: bool
    has_audit_required_transition: bool
    has_idempotency_requirement: bool
    has_ttl_replay_requirement: bool
    has_invalid_direct_callback_to_final_block: bool
    has_invalid_duplicate_callback_accept_block: bool
    has_invalid_replay_accept_block: bool
    has_invalid_expired_to_approved_block: bool
    attempted_payload_creation_transition: bool = False
    attempted_xaman_api_transition: bool = False
    attempted_signing_submission_transition: bool = False
    attempted_wallet_material_transition: bool = False
    attempted_runtime_state_machine_marker: bool = False
    attempted_db_write_persistence_marker: bool = False
    attempted_testnet_live_execution_marker: bool = False


@dataclass(frozen=True)
class XamanApprovalStateMachineSpecReport:
    fixture_id: str
    spec: XamanApprovalStateMachineSpec
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
