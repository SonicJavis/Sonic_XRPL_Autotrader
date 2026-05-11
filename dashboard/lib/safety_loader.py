from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
ARTIFACTS = ROOT / "artifacts"
DOC_AUDIT = ROOT / "docs" / "audit"

PASS = "pass"
FAIL = "fail"
REVIEW = "review"


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _check_from_bool(ok: bool | None, pass_reason: str, fail_reason: str, missing_reason: str) -> dict[str, str]:
    if ok is True:
        return {"status": PASS, "reason": pass_reason}
    if ok is False:
        return {"status": FAIL, "reason": fail_reason}
    return {"status": REVIEW, "reason": missing_reason}


def load_safety_snapshot() -> dict[str, Any]:
    phase56_path = REPORTS / "phase56" / "latest_calibration_implementation_plan.json"
    phase55_path = REPORTS / "phase55" / "latest_calibration_approval_ledger.json"
    audit_path = ARTIFACTS / "audit_validator_report.json"
    dep_path = DOC_AUDIT / "latest_dependency_audit.json"

    phase56 = _load_json(phase56_path)
    approval55 = _load_json(phase55_path)
    audit_validator = _load_json(audit_path)
    dep_audit = _load_json(dep_path)

    checks: dict[str, dict[str, str]] = {}
    checks["Kill Switch State"] = _check_from_bool(
        None if not isinstance(phase56, dict) else phase56.get("live_execution_allowed") is False,
        "Live execution remains blocked",
        "Live execution guard not blocked",
        "Phase 56 artifact missing or unreadable",
    )
    checks["ExecutionGuard"] = _check_from_bool(
        None if not isinstance(phase56, dict) else phase56.get("live_execution_allowed") is False,
        "Fail-closed execution boundary asserted",
        "Execution boundary evidence indicates non-blocked path",
        "Execution guard evidence unavailable",
    )
    checks["live_guard"] = _check_from_bool(
        None if not isinstance(phase56, dict) else phase56.get("runtime_mutation_allowed") is False,
        "Submission/sign/autofill path blocked",
        "Runtime mutation guard not blocked",
        "live_guard evidence unavailable",
    )
    checks["Audit Validator"] = _check_from_bool(
        None if not isinstance(audit_validator, dict) else audit_validator.get("overall_passed") is True,
        "Audit validator report passed",
        "Audit validator report failed",
        "audit_validator_report.json missing or unreadable",
    )
    checks["Safety Scan"] = _check_from_bool(
        None if not isinstance(approval55, dict) else approval55.get("live_execution_allowed") is False,
        "Governance artifacts keep live execution blocked",
        "Governance artifact indicates non-blocked live execution",
        "Phase 55 approval artifact missing or unreadable",
    )
    checks["Dependency Audit"] = _check_from_bool(
        None if not isinstance(dep_audit, dict) else str(dep_audit.get("overall_status", "")).lower() == "pass",
        "Dependency audit passed",
        "Dependency audit failed",
        "latest_dependency_audit.json missing or unreadable",
    )

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
