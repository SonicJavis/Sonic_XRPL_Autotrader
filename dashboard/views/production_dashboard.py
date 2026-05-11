from __future__ import annotations

import streamlit as st

from dashboard.lib.artifact_formatting import normalize_display_value
from dashboard.lib.canonical_loader import load_production_snapshot
from dashboard.lib.ui_components import render_artifact_expander, render_kpi_card, render_page_header


def render_production_dashboard() -> None:
    payload = load_production_snapshot()
    render_page_header(
        "Production Dashboard",
        "Read-only paper-runtime metrics from immutable report artifacts.",
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Alpha Score", payload.get("alpha_score"), helper="24h proxy")
    with c2:
        blocked_value = payload.get("risk_blocked")
        blocked_helper = "paper/runtime reports" if blocked_value is not None else "No runtime report found"
        render_kpi_card(
            "Risk Decisions Blocked",
            blocked_value if blocked_value is not None else "Unknown",
            helper=blocked_helper,
        )
    with c3:
        render_kpi_card("Risk Decisions Allowed", payload.get("risk_allowed"), helper="paper/runtime reports")
    with c4:
        render_kpi_card("Paper PnL Attribution", payload.get("paper_pnl_attribution"), helper="paper-only attribution")

    st.subheader("Signal Review Status")
    line1, line2, line3 = st.columns(3)
    signal_status = payload.get("signal_status")
    readable_status = (
        str(signal_status).replace("_", " ").title() if signal_status not in (None, "") else "Unavailable"
    )
    has_signal = signal_status is not None
    line1.metric("Status", readable_status)
    line2.metric("Badge", "Paper-only" if has_signal else "No report")
    line3.metric("Lineage", "Found" if has_signal else "Missing")
    st.caption(payload.get("signal_lineage_note", "No source-backed signal review artifact found."))

    st.subheader("Artifact Availability")
    availability = payload.get("artifact_availability", {})
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Signal artifact", "Found" if availability.get("signal_artifact") else "Missing")
    a2.metric("Outcome artifact", "Found" if availability.get("outcome_artifact") else "Missing")
    a3.metric("Calibration artifact", "Found" if availability.get("calibration_artifact") else "Missing")
    a4.metric("Source type", normalize_display_value(availability.get("source_type")))

    render_artifact_expander(
        "Raw Signal Review Artifact",
        payload.get("raw_signal_artifact"),
        payload.get("raw_signal_source_path"),
    )

    st.caption(
        "This dashboard is read-only. No execution, signing, submission, or calibration mutation is available."
    )


def main() -> None:
    st.set_page_config(page_title="Production Dashboard", page_icon="S", layout="wide")
    render_production_dashboard()


if __name__ == "__main__":
    main()
