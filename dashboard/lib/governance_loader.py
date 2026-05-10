from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _count(value: Any) -> int | None:
    if isinstance(value, list):
        return len(value)
    return None


def load_governance_snapshot() -> dict[str, Any]:
    p53 = _load_json(REPORTS / "phase53" / "calibration_readiness.json")
    p54 = _load_json(REPORTS / "phase54" / "calibration_proposal_pack.json")
    p55 = _load_json(REPORTS / "phase55" / "latest_calibration_approval_ledger.json")
    p55_cr = _load_json(REPORTS / "phase55" / "latest_calibration_change_requests.json")
    p56 = _load_json(REPORTS / "phase56" / "latest_calibration_implementation_plan.json")

    readiness = (p53 or {}).get("readiness_result", {}) if isinstance(p53, dict) else {}
    summary = {
        "calibration_queue": _count((p53 or {}).get("recommendations")) if isinstance(p53, dict) else None,
        "proposal_records": _count((p54 or {}).get("proposals")) if isinstance(p54, dict) else None,
        "approval_records": _count((p55 or {}).get("records")) if isinstance(p55, dict) else None,
        "phase56_items": _count((p56 or {}).get("implementation_items")) if isinstance(p56, dict) else None,
    }
    lineage = [
        ("Phase 53: Readiness Review", p53 is not None, "Advisory readiness output for human review"),
        ("Phase 54: Proposal Pack", p54 is not None, "Proposed-only calibration packet"),
        ("Phase 55: Approval Ledger", p55 is not None, "Human approval/change-request ledger"),
        ("Phase 56: Implementation Plan", p56 is not None, "Dry-run implementation planning only"),
    ]
    return {
        "summary": summary,
        "phase56_plan": {
            "dry_run_only": (p56 or {}).get("dry_run_only") if isinstance(p56, dict) else None,
            "runtime_mutation_allowed": (p56 or {}).get("runtime_mutation_allowed") if isinstance(p56, dict) else None,
            "implementation_items": _count((p56 or {}).get("implementation_items")) if isinstance(p56, dict) else None,
            "blocked_items": _count((p56 or {}).get("blocked_items")) if isinstance(p56, dict) else None,
            "plan_id": (p56 or {}).get("plan_id") if isinstance(p56, dict) else None,
            "status": readiness.get("status") if isinstance(readiness, dict) else None,
        },
        "lineage": lineage,
        "raw": {"phase53": p53, "phase54": p54, "phase55": p55, "phase55_cr": p55_cr, "phase56": p56},
    }
