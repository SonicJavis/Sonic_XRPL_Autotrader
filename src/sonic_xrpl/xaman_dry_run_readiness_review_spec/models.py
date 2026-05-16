from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

READINESS_SPEC_VALID = "READINESS_SPEC_VALID"
READINESS_SPEC_REVIEW_REQUIRED = "READINESS_SPEC_REVIEW_REQUIRED"
READINESS_SPEC_INVALID = "READINESS_SPEC_INVALID"
READINESS_BLOCKED = "READINESS_BLOCKED"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class Phase69SafetyFlags:
    dry_run_readiness_spec_only: bool = True
    runtime_dry_run_runner_allowed: bool = False
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
class ReadinessRequirement:
    key: str
    label: str
    required: bool
    rationale: str


@dataclass(frozen=True)
class Phase69Blocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_runtime_implementation: bool
    required_before_testnet_implementation: bool
    required_before_live_implementation: bool


@dataclass(frozen=True)
class XamanDryRunReadinessReviewSpec:
    phase: str
    objective: str
    readiness_pack_id: str
    candidate_id: str
    readiness_requirements: tuple[ReadinessRequirement, ...]
    completeness_requirements: tuple[str, ...]
    blockers: tuple[Phase69Blocker, ...] = field(default_factory=tuple)
    safety_flags: Phase69SafetyFlags = Phase69SafetyFlags()


@dataclass(frozen=True)
class XamanDryRunReadinessFixtureInput:
    fixture_id: str
    readiness_pack_id: str
    candidate_id: str
    has_manual_approval_design_reference: bool
    has_payload_schema_spec_reference: bool
    has_callback_verification_spec_reference: bool
    has_audit_idempotency_spec_reference: bool
    has_approval_state_machine_spec_reference: bool
    has_operator_consent_ux_reference: bool
    has_consent_evidence_pack_reference: bool
    has_preflight_safety_checklist_reference: bool
    has_dependency_audit_status: bool
    has_safety_grep_status: bool
    has_audit_validator_status: bool
    has_migration_safe_status: bool
    has_guard_critical_status: bool
    has_no_secrets_status: bool
    has_no_wallet_material_status: bool
    has_no_xaman_api_status: bool
    has_no_payload_created_status: bool
    has_no_signing_submission_status: bool
    has_no_testnet_execution_status: bool
    has_no_live_execution_status: bool
    has_rollback_plan_status: bool
    has_kill_switch_design_status: bool
    invalid_payload_created_marker: bool = False
    invalid_xaman_called_marker: bool = False
    invalid_signing_submission_marker: bool = False
    invalid_wallet_material_marker: bool = False
    invalid_runtime_runner_marker: bool = False
    invalid_ui_api_runtime_marker: bool = False
    invalid_export_file_write_marker: bool = False
    invalid_persistence_db_write_marker: bool = False
    invalid_testnet_live_execution_marker: bool = False
    invalid_testnet_approved_marker: bool = False
    invalid_live_approved_marker: bool = False


@dataclass(frozen=True)
class XamanDryRunReadinessSpecReport:
    fixture_id: str
    spec: XamanDryRunReadinessReviewSpec
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
