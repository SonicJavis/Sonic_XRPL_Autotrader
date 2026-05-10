from __future__ import annotations

import streamlit as st

from dashboard.artifacts import REPORTS, load_json


def _metric_or_missing(label: str, value: object, fmt: str | None = None) -> None:
    if value is None:
        st.metric(label, "no artifact available")
        return
    if isinstance(value, float) and fmt is not None:
        st.metric(label, format(value, fmt))
        return
    st.metric(label, str(value))


def render_production_dashboard() -> None:
    st.title("Production Dashboard")
    st.caption("Read-only production paper metrics from immutable report artifacts.")

    market_rows = load_json(REPORTS / "phase47" / "market_snapshot_042b75dbd2a2_20260503T121647Z.json")
    quality_rows = load_json(REPORTS / "phase52" / "outcome_corpus_quality.json")
    signal_review = load_json(REPORTS / "phase53" / "calibration_readiness.json")

    alpha_score = None
    if isinstance(market_rows, dict) and "aggregate_score" in market_rows:
        alpha_score = float(market_rows.get("aggregate_score", 0.0))

    blocked = None
    allowed = None
    if isinstance(signal_review, dict):
        blocked = int(signal_review.get("blocked_count", 0))
        allowed = int(signal_review.get("ready_count", 0))

    paper_pnl = None
    if isinstance(quality_rows, dict) and "aggregate_realized_pnl" in quality_rows:
        paper_pnl = float(quality_rows.get("aggregate_realized_pnl", 0.0))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_or_missing("Alpha Score (24h proxy)", alpha_score, ".4f")
    with c2:
        _metric_or_missing("Risk Decisions Blocked", blocked)
    with c3:
        _metric_or_missing("Risk Decisions Allowed", allowed)
    with c4:
        _metric_or_missing("Paper PnL Attribution", paper_pnl, ".4f")

    st.subheader("Signal Review Status (Phase 49-50 lineage)")
    if isinstance(signal_review, dict):
        row1, row2, row3 = st.columns(3)
        row1.metric("Readiness Status", str(signal_review.get("status", "no artifact available")))
        row2.metric("Blocked Count", str(signal_review.get("blocked_count", "no artifact available")))
        row3.metric("Recommendations", str(signal_review.get("recommendation_count", "no artifact available")))
        with st.expander("Signal Review Artifact (Raw JSON)"):
            st.json(signal_review)
    else:
        st.info("no artifact available")

    st.caption("No execution triggers available.")


def main() -> None:
    st.set_page_config(page_title="Production Dashboard", page_icon="S", layout="wide")
    render_production_dashboard()


if __name__ == "__main__":
    main()
