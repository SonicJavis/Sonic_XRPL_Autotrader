from __future__ import annotations

import math
from typing import Any, Mapping

from sonic_xrpl.calibration_implementation_plan.dry_run_patch import build_patch_preview
from sonic_xrpl.calibration_implementation_plan.loader import load_approval_ledger, load_change_requests
from sonic_xrpl.calibration_implementation_plan.models import (
    BlockedImplementationItem,
    CalibrationImplementationItem,
    CalibrationImplementationPlan,
    DETERMINISTIC_CREATED_AT,
    PHASE,
)
from sonic_xrpl.calibration_implementation_plan.rollback_plan import build_rollback_plan
from sonic_xrpl.calibration_implementation_plan.validation_plan import build_validation_plan
from sonic_xrpl.signals.evidence import stable_id


SUPPORTED_PARAMETERS = {
    "signal_score_threshold",
    "risk_score_threshold",
    "watch_threshold",
    "avoid_threshold",
    "evidence_quality_threshold",
    "unknown_penalty",
    "synthetic_penalty",
}
TARGET_FILE_HINT = "config/paper_calibration_thresholds.json (future phase)"
TARGET_NAMESPACE = "paper_calibration"


def _bool_flag(payload: Mapping[str, Any], key: str, default: bool = False) -> bool:
    value = payload.get(key, default)
    return bool(value)


def _request_is_safe(payload: Mapping[str, Any]) -> tuple[bool, str]:
    checks = (
        ("paper_only", True),
        ("offline_only", True),
        ("apply_allowed", False),
        ("live_execution_allowed", False),
        ("runtime_mutation_allowed", False),
    )
    for key, expected in checks:
        actual = _bool_flag(payload, key, not expected)
        if actual != expected:
            return False, f"unsafe_flag_{key}"
    return True, ""


def _as_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _extract_parameter_name(change_request: Mapping[str, Any]) -> str:
    requested = str(change_request.get("requested_change") or "")
    if ":" in requested:
        return requested.split(":", 1)[0].strip()
    return str(change_request.get("target_parameter") or "").strip()


def _proposal_record_by_id(ledger: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    items = ledger.get("records", [])
    mapped: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list):
        return mapped
    for item in items:
        if isinstance(item, Mapping):
            proposal_id = str(item.get("proposal_id") or "")
            if proposal_id:
                mapped[proposal_id] = dict(item)
    return mapped


def build_calibration_implementation_plan(
    approval_ledger_path: str,
    change_requests_path: str,
) -> CalibrationImplementationPlan:
    ledger = load_approval_ledger(approval_ledger_path)
    requests = load_change_requests(change_requests_path)
    records_by_proposal = _proposal_record_by_id(ledger)
    implementation_items: list[CalibrationImplementationItem] = []
    blocked_items: list[BlockedImplementationItem] = []

    for request in requests:
        change_request_id = str(request.get("change_request_id") or "")
        proposal_id = str(request.get("proposal_id") or "")
        if not change_request_id or not proposal_id:
            blocked_items.append(
                BlockedImplementationItem(
                    change_request_id=change_request_id or "missing_change_request_id",
                    proposal_id=proposal_id or "missing_proposal_id",
                    reason="missing_required_ids",
                    limitations=("change_request_id and proposal_id are required.",),
                    required_next_action="Provide explicit proposal_id and change_request_id in the Phase 55 change request record.",
                )
            )
            continue

        safe, unsafe_reason = _request_is_safe(request)
        if not safe:
            blocked_items.append(
                BlockedImplementationItem(
                    change_request_id=change_request_id,
                    proposal_id=proposal_id,
                    reason=unsafe_reason,
                    limitations=("Phase 56 accepts planning input only when all safety flags are strict false/true values.",),
                    required_next_action="Regenerate Phase 55 change requests with paper-only, offline-only, and non-mutating safety flags.",
                )
            )
            continue

        if str(request.get("status") or "").upper() != "REQUESTED":
            blocked_items.append(
                BlockedImplementationItem(
                    change_request_id=change_request_id,
                    proposal_id=proposal_id,
                    reason="unsupported_change_request_status",
                    limitations=("Only REQUESTED change requests can be planned in Phase 56.",),
                    required_next_action="Use explicitly REQUESTED change requests for implementation planning.",
                )
            )
            continue

        parameter_name = _extract_parameter_name(request)
        if parameter_name not in SUPPORTED_PARAMETERS:
            blocked_items.append(
                BlockedImplementationItem(
                    change_request_id=change_request_id,
                    proposal_id=proposal_id,
                    reason="unsupported_target_parameter",
                    limitations=(f"Unsupported parameter: {parameter_name or 'missing'}",),
                    required_next_action="Use one of the supported Phase 56 planning parameters.",
                )
            )
            continue

        before_value = _as_float(request.get("before_value"))
        after_value = _as_float(request.get("after_value"))
        delta = _as_float(request.get("delta"))
        if before_value is None or after_value is None or delta is None:
            blocked_items.append(
                BlockedImplementationItem(
                    change_request_id=change_request_id,
                    proposal_id=proposal_id,
                    reason="invalid_numeric_values",
                    limitations=("before_value, after_value, and delta must be finite numbers.",),
                    required_next_action="Fix the numeric values in Phase 55 change request artifacts before planning implementation.",
                )
            )
            continue

        computed_delta = round(after_value - before_value, 10)
        if abs(computed_delta - delta) > 1e-9:
            blocked_items.append(
                BlockedImplementationItem(
                    change_request_id=change_request_id,
                    proposal_id=proposal_id,
                    reason="delta_mismatch",
                    limitations=("delta must equal after_value - before_value.",),
                    required_next_action="Regenerate the change request with a consistent numeric delta.",
                )
            )
            continue

        record = records_by_proposal.get(proposal_id, {})
        item_id = stable_id("cpi", change_request_id, proposal_id, parameter_name, before_value, after_value)
        config_key = f"{TARGET_NAMESPACE}.{parameter_name}"
        item = CalibrationImplementationItem(
            implementation_item_id=item_id,
            change_request_id=change_request_id,
            proposal_id=proposal_id,
            target_namespace=TARGET_NAMESPACE,
            target_parameter=parameter_name,
            current_value=before_value,
            proposed_value=after_value,
            exact_delta=delta,
            implementation_status="DRY_RUN_PLANNED",
            target_file_hint=TARGET_FILE_HINT,
            target_config_key_hint=config_key,
            dry_run_diff="",
            validation_commands=build_validation_plan().required_commands,
            rollback_note=(
                "No runtime change exists in Phase 56. "
                "Rollback by reverting future implementation commit(s) only."
            ),
            safety_flags={
                "paper_only": True,
                "offline_only": True,
                "dry_run_only": True,
                "auto_apply_allowed": False,
                "live_execution_allowed": False,
                "runtime_mutation_allowed": False,
                "requires_human_implementation": True,
            },
            limitations=tuple(
                dict.fromkeys(
                    [
                        "dry_run_only_no_runtime_mutation",
                        *[str(item) for item in (record.get("limitation_summary") or []) if str(item)],
                    ]
                )
            ),
        )
        preview = build_patch_preview(item)
        implementation_items.append(
            CalibrationImplementationItem(
                **{**item.__dict__, "dry_run_diff": preview.diff_text}
            )
        )

    plan_id = stable_id(
        "cip",
        ledger.get("ledger_id", ""),
        tuple(item.implementation_item_id for item in implementation_items),
        tuple(item.change_request_id for item in blocked_items),
    )
    validation_plan = build_validation_plan()
    rollback_plan = build_rollback_plan()
    patches = tuple(build_patch_preview(item) for item in implementation_items)
    limitations = tuple(
        dict.fromkeys(
            [*("No implementation patch is applied in Phase 56.",), *(item.reason for item in blocked_items)]
        )
    )
    return CalibrationImplementationPlan(
        plan_id=plan_id,
        created_at=DETERMINISTIC_CREATED_AT,
        phase=PHASE,
        source_ledger_id=str(ledger.get("ledger_id") or ""),
        source_change_request_count=len(requests),
        implementation_items=tuple(implementation_items),
        blocked_items=tuple(blocked_items),
        dry_run_patches=patches,
        validation_plan=validation_plan,
        rollback_plan=rollback_plan,
        safety_summary=(
            "Phase 56 implementation planning is offline, paper-only, dry-run-only, and non-mutating. "
            "No configuration file or runtime threshold is changed. Live execution remains blocked."
        ),
        limitations=limitations,
        paper_only=True,
        offline_only=True,
        dry_run_only=True,
        auto_apply_allowed=False,
        live_execution_allowed=False,
        runtime_mutation_allowed=False,
        requires_human_implementation=True,
    )
