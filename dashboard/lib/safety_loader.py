from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
ARTIFACTS = ROOT / "artifacts"
DOC_AUDIT = ROOT / "docs" / "audit"


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_safety_snapshot() -> dict[str, Any]:
    phase56 = _load_json(REPORTS / "phase56" / "latest_calibration_implementation_plan.json")
    approval55 = _load_json(REPORTS / "phase55" / "latest_calibration_approval_ledger.json")
    audit_validator = _load_json(ARTIFACTS / "audit_validator_report.json")
    dep_audit = _load_json(DOC_AUDIT / "latest_dependency_audit.json")

    kill_switch = bool(phase56 and phase56.get("live_execution_allowed") is False)
    execution_guard = bool(phase56 and phase56.get("live_execution_allowed") is False)
    live_guard = bool(phase56 and phase56.get("runtime_mutation_allowed") is False)
    audit_ok = bool(isinstance(audit_validator, dict) and audit_validator.get("overall_passed") is True)
    safety_scan_ok = bool(approval55 and approval55.get("live_execution_allowed") is False)
    dep_ok = bool(isinstance(dep_audit, dict) and dep_audit.get("overall_status") == "pass")

    checks = {
        "Kill Switch State": (kill_switch, "Phase 56 report enforces blocked live execution"),
        "ExecutionGuard": (execution_guard, "Fail-closed execution boundary"),
        "live_guard": (live_guard, "Submission/sign/autofill path blocked"),
        "Audit Validator": (audit_ok, "Audit report status"),
        "Safety Scan": (safety_scan_ok, "Phase 55/56 live execution blocked"),
        "Dependency Audit": (dep_ok, "Dependency audit status"),
    }

    overall = all(ok for ok, _ in checks.values())
    status = "pass" if overall else "fail"
    return {
        "overall_status": status,
        "checks": checks,
        "artifacts": {
            "phase56": str(REPORTS / "phase56" / "latest_calibration_implementation_plan.json"),
            "phase55": str(REPORTS / "phase55" / "latest_calibration_approval_ledger.json"),
            "audit_validator_report": str(ARTIFACTS / "audit_validator_report.json"),
            "dependency_audit_report": str(DOC_AUDIT / "latest_dependency_audit.json"),
        },
        "raw": {
            "phase56": phase56,
            "phase55": approval55,
            "audit_validator": audit_validator,
            "dependency_audit": dep_audit,
        },
    }
