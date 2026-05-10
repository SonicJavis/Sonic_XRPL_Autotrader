from __future__ import annotations

import streamlit as st

from dashboard.artifacts import DOCS, REPORTS, load_json


def _status_color(ok: bool) -> str:
    return "🟢 PASS" if ok else "🔴 FAIL"


def main() -> None:
    st.set_page_config(page_title="Safety Status", page_icon="S", layout="wide")
    st.title("Safety Status")
    st.caption("Read-only red/green safety board.")

    phase56 = load_json(REPORTS / "phase56" / "latest_calibration_implementation_plan.json") or {}
    approval55 = load_json(REPORTS / "phase55" / "latest_calibration_approval_ledger.json") or {}

    kill_switch_ok = bool(phase56.get("live_execution_allowed") is False)
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
    s1.metric("Kill Switch State", _status_color(kill_switch_ok))
    s2.metric("ExecutionGuard", _status_color(execution_guard_ok))
    s3.metric("live_guard", _status_color(live_guard_ok))
    s4.metric("Audit Validator", _status_color(audit_ok))
    s5.metric("Safety Scan", _status_color(safety_scan_ok))


if __name__ == "__main__":
    main()
