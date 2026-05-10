from __future__ import annotations

import streamlit as st

from dashboard.artifacts import REPORTS, load_json, to_count


def main() -> None:
    st.set_page_config(page_title="Governance Status", page_icon="S", layout="wide")
    st.title("Governance Status (Phase 53-56)")
    st.caption("Calibration queue, proposal/approval status, and implementation planning state.")

    p53 = load_json(REPORTS / "phase53" / "calibration_readiness.json") or {}
    p54 = load_json(REPORTS / "phase54" / "calibration_proposal_pack.json") or {}
    p55 = load_json(REPORTS / "phase55" / "latest_calibration_approval_ledger.json") or {}
    p55_cr = load_json(REPORTS / "phase55" / "latest_calibration_change_requests.json") or {}
    p56 = load_json(REPORTS / "phase56" / "latest_calibration_implementation_plan.json") or {}

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Calibration Queue", str(p53.get("queued_recommendations", "no artifact available")))
    q2.metric("Proposal Records", str(to_count(p54.get("proposals", []) if isinstance(p54, dict) else [])))
    q3.metric("Approval Records", str(to_count(p55.get("records", []) if isinstance(p55, dict) else [])))
    q4.metric("Phase 56 Items", str(to_count(p56.get("implementation_items", []) if isinstance(p56, dict) else [])))

    st.subheader("Proposal / Approval / Change Requests")
    c1, c2, c3 = st.columns(3)
    c1.metric("Approved Requests", str(len(p55_cr.get("change_requests", [])) if isinstance(p55_cr, dict) else 0))
    c2.metric("Blocked Plan Items", str(len(p56.get("blocked_items", [])) if isinstance(p56, dict) else 0))
    c3.metric("Dry Run Only", "true" if p56.get("dry_run_only") else "false")

    st.subheader("Phase 56 Plan")
    if p56:
        summary_cols = st.columns(3)
        summary_cols[0].metric("Plan ID", str(p56.get("plan_id", "no artifact available")))
        summary_cols[1].metric("Blocked Items", str(to_count(p56.get("blocked_items", []))))
        summary_cols[2].metric("Human Implementation", str(bool(p56.get("requires_human_implementation"))).lower())
        with st.expander("Phase 56 Plan Artifact (Raw JSON)"):
            st.json(p56)
    else:
        st.info("No Phase 56 plan report found.")

    with st.expander("Phase 53 Artifact (Raw JSON)"):
        if p53:
            st.json(p53)
        else:
            st.caption("no artifact available")
    with st.expander("Phase 54 Artifact (Raw JSON)"):
        if p54:
            st.json(p54)
        else:
            st.caption("no artifact available")
    with st.expander("Phase 55 Ledger Artifact (Raw JSON)"):
        if p55:
            st.json(p55)
        else:
            st.caption("no artifact available")
    with st.expander("Phase 55 Change Requests Artifact (Raw JSON)"):
        if p55_cr:
            st.json(p55_cr)
        else:
            st.caption("no artifact available")


if __name__ == "__main__":
    main()
