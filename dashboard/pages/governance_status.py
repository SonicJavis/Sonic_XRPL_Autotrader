from __future__ import annotations

import streamlit as st

from dashboard.lib.artifact_formatting import normalize_display_value
from dashboard.lib.governance_loader import load_governance_snapshot
from dashboard.lib.ui_components import render_page_header, status_to_color


def main() -> None:
    st.set_page_config(page_title="Governance Status", page_icon="S", layout="wide")
    payload = load_governance_snapshot()

    render_page_header(
        "Governance Status",
        "Human-reviewed calibration lineage and dry-run implementation planning.",
    )

    summary = payload.get("summary", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Calibration Queue", normalize_display_value(summary.get("calibration_queue")))
    c2.metric("Proposal Records", normalize_display_value(summary.get("proposal_records")))
    c3.metric("Approval Records", normalize_display_value(summary.get("approval_records")))
    c4.metric("Phase 56 Items", normalize_display_value(summary.get("phase56_items")))

    st.subheader("Phase Lineage")
    for label, found, desc in payload.get("lineage", []):
        status = "pass" if found else "fail"
        st.markdown(f"**{label}**  {status_to_color(status)}  \n{desc}")

    st.subheader("Phase 56 Plan")
    p56 = payload.get("phase56_plan", {})
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Dry-run-only", normalize_display_value(p56.get("dry_run_only")))
    p2.metric("Runtime mutation", normalize_display_value(p56.get("runtime_mutation_allowed")))
    p3.metric("Implementation items", normalize_display_value(p56.get("implementation_items")))
    p4.metric("Blocked items", normalize_display_value(p56.get("blocked_items")))
    st.caption(f"Plan ID: {normalize_display_value(p56.get('plan_id'))}")

    with st.expander("Raw Governance Artifacts", expanded=False):
        st.json(payload.get("raw"))

    st.caption("Governance artifacts are advisory and do not mutate runtime configuration.")


if __name__ == "__main__":
    main()
