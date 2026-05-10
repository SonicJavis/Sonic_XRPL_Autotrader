from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
PHASE = "56"


@dataclass(frozen=True)
class DryRunPatchPreview:
    patch_id: str
    target_file_hint: str
    target_config_key_hint: str
    before_value: float
    after_value: float
    diff_text: str
    apply_allowed: bool = False
    runtime_mutation_allowed: bool = False


@dataclass(frozen=True)
class CalibrationImplementationItem:
    implementation_item_id: str
    change_request_id: str
    proposal_id: str
    target_namespace: str
    target_parameter: str
    current_value: float
    proposed_value: float
    exact_delta: float
    implementation_status: str
    target_file_hint: str
    target_config_key_hint: str
    dry_run_diff: str
    validation_commands: tuple[str, ...]
    rollback_note: str
    safety_flags: dict[str, bool]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class BlockedImplementationItem:
    change_request_id: str
    proposal_id: str
    reason: str
    limitations: tuple[str, ...]
    required_next_action: str


@dataclass(frozen=True)
class ImplementationValidationPlan:
    required_commands: tuple[str, ...]
    required_tests: tuple[str, ...]
    safety_checks: tuple[str, ...]
    docs_checks: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]


@dataclass(frozen=True)
class ImplementationRollbackPlan:
    rollback_id: str
    rollback_steps: tuple[str, ...]
    affected_files: tuple[str, ...]
    requires_manual_review: bool = True


@dataclass(frozen=True)
class CalibrationImplementationPlan:
    plan_id: str
    created_at: str
    phase: str
    source_ledger_id: str
    source_change_request_count: int
    implementation_items: tuple[CalibrationImplementationItem, ...]
    blocked_items: tuple[BlockedImplementationItem, ...]
    dry_run_patches: tuple[DryRunPatchPreview, ...]
    validation_plan: ImplementationValidationPlan
    rollback_plan: ImplementationRollbackPlan
    safety_summary: str
    limitations: tuple[str, ...]
    paper_only: bool = True
    offline_only: bool = True
    dry_run_only: bool = True
    auto_apply_allowed: bool = False
    live_execution_allowed: bool = False
    runtime_mutation_allowed: bool = False
    requires_human_implementation: bool = True


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: jsonable(getattr(value, key))
            for key in value.__dataclass_fields__
        }
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value
