from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PREFLIGHT_SPEC_VALID = "PREFLIGHT_SPEC_VALID"
PREFLIGHT_SPEC_REVIEW_REQUIRED = "PREFLIGHT_SPEC_REVIEW_REQUIRED"
PREFLIGHT_SPEC_INVALID = "PREFLIGHT_SPEC_INVALID"
PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Phase68SafetyFlags:
    preflight_spec_only: bool = True
    runtime_checklist_runner_allowed: bool = False
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
class ChecklistRequirement:
    key: str
    label: str
    required: bool
    rationale: str


@dataclass(frozen=True)
class Phase68Blocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_runtime_implementation: bool
    required_before_testnet_implementation: bool
    required_before_live_implementation: bool


@dataclass(frozen=True)
class XamanPreflightSafetyChecklistSpec:
    phase: str
    objective: str
    checklist_id: str
    candidate_id: str
    checklist_requirements: tuple[ChecklistRequirement, ...]
    completeness_requirements: tuple[str, ...]
    blockers: tuple[Phase68Blocker, ...] = field(default_factory=tuple)
    safety_flags: Phase68SafetyFlags = Phase68SafetyFlags()


@dataclass(frozen=True)
class XamanPreflightSafetyChecklistFixtureInput:
    fixture_id: str
    checklist_id: str
    candidate_id: str
    has_evidence_pack_gate: bool
    has_payload_schema_gate: bool
    has_callback_verification_gate: bool
    has_audit_idempotency_gate: bool
    has_approval_state_machine_gate: bool
    has_operator_consent_ux_gate: bool
    has_dependency_audit_gate: bool
    has_safety_grep_gate: bool
    has_audit_validator_gate: bool
    has_migration_safe_gate: bool
    has_guard_critical_gate: bool
    has_no_secrets_gate: bool
    has_no_wallet_material_gate: bool
    has_no_xaman_api_gate: bool
    has_no_payload_created_gate: bool
    has_no_signing_submission_gate: bool
    has_no_testnet_execution_gate: bool
    has_no_live_execution_gate: bool
    has_rollback_plan: bool
    has_kill_switch_design: bool
    invalid_payload_created_marker: bool = False
    invalid_xaman_called_marker: bool = False
    invalid_signing_submission_marker: bool = False
    invalid_wallet_material_marker: bool = False
    invalid_runtime_runner_marker: bool = False
    invalid_ui_api_runtime_marker: bool = False
    invalid_export_file_write_marker: bool = False
    invalid_persistence_db_write_marker: bool = False
    invalid_testnet_live_execution_marker: bool = False


@dataclass(frozen=True)
class XamanPreflightSafetyChecklistSpecReport:
    fixture_id: str
    spec: XamanPreflightSafetyChecklistSpec
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
