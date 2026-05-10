from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> None:
    st.set_page_config(page_title="Sonic XRPL Operator Dashboard", page_icon="S", layout="wide")
    st.title("Sonic XRPL Operator Dashboard")
    st.caption("Canonical source: `src/sonic_xrpl` reports and safety outputs (read-only).")

    st.error("Live execution: BLOCKED")
    st.warning("No execution triggers are available in this dashboard.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Runtime Mode", "paper")
    c2.metric("Execution Enabled", "false")
    c3.metric("Live Trading Enabled", "false")

    st.subheader("Phase Governance Snapshot")
    readiness = _load_json(REPORTS / "phase53" / "calibration_readiness.json")
    proposal = _load_json(REPORTS / "phase54" / "calibration_proposal_pack.json")
    approvals = _load_json(REPORTS / "phase55" / "latest_calibration_approval_ledger.json")
    plan56 = _load_json(REPORTS / "phase56" / "latest_calibration_implementation_plan.json")

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Phase 53", "ready" if readiness else "missing")
    g2.metric("Phase 54", "ready" if proposal else "missing")
    g3.metric("Phase 55", "ready" if approvals else "missing")
    g4.metric("Phase 56", "ready" if plan56 else "missing")

    st.subheader("Navigation")
    st.markdown(
        "- Open **Production Dashboard** for alpha/risk/paper attribution views.\n"
        "- Open **Safety Status** for kill-switch and guard status checks.\n"
        "- Open **Governance Status** for Phase 53-56 queue/proposal/approval/plan views."
    )


if __name__ == "__main__":
    main()
