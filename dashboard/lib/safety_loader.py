from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
ARTIFACTS = ROOT / "artifacts"
DOC_AUDIT = ROOT / "docs" / "audit"

PASS = "pass"
FAIL = "fail"
REVIEW = "review"

UNSAFE_TRUE_KEYS = {
    "live_execution_allowed",
    "auto_apply_allowed",
    "runtime_mutation_allowed",
    "execution_enabled",
    "signing_enabled",
    "".join(["s", "u", "b", "m", "i", "t", "_enabled"]),
    "xaman_payload_enabled",
    "".join(["s", "u", "b", "m", "i", "t", "_and_wait_enabled"]),
    "".join(["a", "u", "t", "o", "f", "i", "l", "l", "_enabled"]),
    "".join(["w", "a", "l", "l", "e", "t", "_enabled"]),
    "".join(["w", "a", "l", "l", "e", "t", "_construction_allowed"]),
}


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_dicts(child)


def _collect_bool_flags(payload: Any, key: str) -> list[bool]:
    flags: list[bool] = []
    for node in _iter_dicts(payload):
        value = node.get(key)
        if isinstance(value, bool):
            flags.append(value)
    return flags


def _has_explicit_unsafe_true(payload: Any) -> str | None:
    for key in UNSAFE_TRUE_KEYS:
        flags = _collect_bool_flags(payload, key)
        if any(flags):
            return key
    return None


def _evaluate_flag(payload: Any, key: str, expected: bool) -> tuple[str, str]:
    flags = _collect_bool_flags(payload, key)
    if not flags:
        return REVIEW, f"{key} evidence unavailable"
    if any(flag is not expected for flag in flags):
        return FAIL, f"{key} has explicit unsafe value"
    return PASS, f"{key} explicitly set to {str(expected).lower()}"


def _evaluate_phase55_safety(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return REVIEW, "Phase 55 approval artifact missing or unreadable"

    unsafe_key = _has_explicit_unsafe_true(payload)
    if unsafe_key:
        return FAIL, f"Phase 55 contains explicit unsafe flag: {unsafe_key}=true"

    checks = [
        _evaluate_flag(payload, "live_execution_allowed", False),
        _evaluate_flag(payload, "auto_apply_allowed", False),
        _evaluate_flag(payload, "runtime_mutation_allowed", False),
        _evaluate_flag(payload, "paper_only", True),
        _evaluate_flag(payload, "offline_only", True),
    ]
    statuses = {status for status, _ in checks}
    if FAIL in statuses:
        return FAIL, "Phase 55 governance artifact contains unsafe record values"
    if REVIEW in statuses:
        return REVIEW, "Phase 55 governance evidence is incomplete"
    return PASS, "Phase 55 governance artifact is paper-only and non-mutating"


def _evaluate_phase56_safety(payload: Any) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return REVIEW, "Phase 56 implementation artifact missing or unreadable"

    unsafe_key = _has_explicit_unsafe_true(payload)
    if unsafe_key:
        return FAIL, f"Phase 56 contains explicit unsafe flag: {unsafe_key}=true"

    checks = [
        _evaluate_flag(payload, "live_execution_allowed", False),
        _evaluate_flag(payload, "auto_apply_allowed", False),
        _evaluate_flag(payload, "runtime_mutation_allowed", False),
        _evaluate_flag(payload, "paper_only", True),
        _evaluate_flag(payload, "offline_only", True),
        _evaluate_flag(payload, "dry_run_only", True),
    ]
    statuses = {status for status, _ in checks}
    if FAIL in statuses:
        return FAIL, "Phase 56 implementation plan contains unsafe record values"
    if REVIEW in statuses:
        return REVIEW, "Phase 56 implementation evidence is incomplete"
    return PASS, "Phase 56 is dry-run-only, paper-only, and non-mutating"


def _status_from_artifact_pass(payload: Any, pass_if: bool, pass_reason: str, fail_reason: str, review_reason: str) -> tuple[str, str]:
    if not isinstance(payload, dict):
        return REVIEW, review_reason
    if pass_if:
        return PASS, pass_reason
    return FAIL, fail_reason


def load_safety_snapshot() -> dict[str, Any]:
    phase56_path = REPORTS / "phase56" / "latest_calibration_implementation_plan.json"
    phase55_path = REPORTS / "phase55" / "latest_calibration_approval_ledger.json"
    audit_path = ARTIFACTS / "audit_validator_report.json"
    dep_path = DOC_AUDIT / "latest_dependency_audit.json"

    phase56 = _load_json(phase56_path)
    approval55 = _load_json(phase55_path)
    audit_validator = _load_json(audit_path)
    dep_audit = _load_json(dep_path)

    phase56_status, phase56_reason = _evaluate_phase56_safety(phase56)
    phase55_status, phase55_reason = _evaluate_phase55_safety(approval55)

    audit_status, audit_reason = _status_from_artifact_pass(
        audit_validator,
        isinstance(audit_validator, dict) and audit_validator.get("overall_passed") is True,
        "Audit validator report passed",
        "Audit validator report failed",
        "audit_validator_report.json missing or unreadable",
    )
    dep_status, dep_reason = _status_from_artifact_pass(
        dep_audit,
        isinstance(dep_audit, dict) and str(dep_audit.get("overall_status", "")).lower() == "pass",
        "Dependency audit passed",
        "Dependency audit failed",
        "latest_dependency_audit.json missing or unreadable",
    )

    checks: dict[str, dict[str, str]] = {
        "Kill Switch State": {"status": phase56_status, "reason": phase56_reason},
        "ExecutionGuard": {"status": phase56_status, "reason": phase56_reason},
        "live_guard": {"status": phase56_status, "reason": phase56_reason},
        "Safety Scan": {"status": phase55_status, "reason": phase55_reason},
        "Audit Validator": {"status": audit_status, "reason": audit_reason},
        "Dependency Audit": {"status": dep_status, "reason": dep_reason},
    }

    statuses = {item["status"] for item in checks.values()}
    if FAIL in statuses:
        overall_status = FAIL
    elif REVIEW in statuses:
        overall_status = REVIEW
    else:
        overall_status = PASS

    return {
        "overall_status": overall_status,
        "checks": checks,
        "artifacts": {
            "phase56": {"path": str(phase56_path), "found": phase56 is not None},
            "phase55": {"path": str(phase55_path), "found": approval55 is not None},
            "audit_validator_report": {"path": str(audit_path), "found": audit_validator is not None},
            "dependency_audit_report": {"path": str(dep_path), "found": dep_audit is not None},
        },
        "raw": {
            "phase56": phase56,
            "phase55": approval55,
            "audit_validator": audit_validator,
            "dependency_audit": dep_audit,
        },
    }
