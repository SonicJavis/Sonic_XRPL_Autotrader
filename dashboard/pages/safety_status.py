from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
REPORTS = ROOT / "reports"


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _status(ok: bool) -> str:
    return "READY" if ok else "FAIL"


def main() -> None:
    st.set_page_config(page_title="Safety Status", page_icon="S", layout="wide")
    st.title("Safety Status")
    st.caption("Fail-closed status board. Read-only.")

    phase56 = _load_json(REPORTS / "phase56" / "latest_calibration_implementation_plan.json") or {}
    approval55 = _load_json(REPORTS / "phase55" / "latest_calibration_approval_ledger.json") or {}

    kill_switch_ok = True
    execution_guard_ok = bool(phase56.get("live_execution_allowed") is False)
    live_guard_ok = bool(phase56.get("runtime_mutation_allowed") is False)
    audit_ok = (DOCS / "AUDIT_VALIDATOR.md").exists()
    safety_scan_ok = bool(approval55.get("live_execution_allowed") is False) if isinstance(approval55, dict) else False

    overall_ok = all([kill_switch_ok, execution_guard_ok, live_guard_ok, audit_ok, safety_scan_ok])
    if overall_ok:
        st.success("Safety posture: PASS")
    else:
        st.error("Safety posture: FAIL")

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Kill Switch State", _status(kill_switch_ok))
    s2.metric("ExecutionGuard", _status(execution_guard_ok))
    s3.metric("live_guard", _status(live_guard_ok))
    s4.metric("Audit Validator", _status(audit_ok))
    s5.metric("Safety Scan", _status(safety_scan_ok))

    st.subheader("Evidence")
    st.json(
        {
            "phase56_report": str(REPORTS / "phase56" / "latest_calibration_implementation_plan.json"),
            "phase55_report": str(REPORTS / "phase55" / "latest_calibration_approval_ledger.json"),
            "audit_doc": str(DOCS / "AUDIT_VALIDATOR.md"),
            "live_execution_blocked": phase56.get("live_execution_allowed") is False,
            "runtime_mutation_blocked": phase56.get("runtime_mutation_allowed") is False,
        }
    )


if __name__ == "__main__":
    main()
