from __future__ import annotations

import json
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def main() -> None:
    st.set_page_config(page_title="Production Dashboard", page_icon="S", layout="wide")
    st.title("Production Dashboard")
    st.caption("Read-only production paper metrics from canonical report artifacts.")

    market_rows = _load_json(REPORTS / "phase47" / "market_snapshot_042b75dbd2a2_20260503T121647Z.json") or {}
    quality_rows = _load_json(REPORTS / "phase52" / "outcome_corpus_quality.json") or {}
    signal_review = _load_json(REPORTS / "phase53" / "calibration_readiness.json") or {}
    implementation = _load_json(REPORTS / "phase56" / "latest_calibration_implementation_plan.json") or {}

    alpha_score = float(market_rows.get("aggregate_score", 0.0)) if isinstance(market_rows, dict) else 0.0
    blocked = int(signal_review.get("blocked_count", 0)) if isinstance(signal_review, dict) else 0
    allowed = int(signal_review.get("ready_count", 0)) if isinstance(signal_review, dict) else 0
    paper_pnl = float(quality_rows.get("aggregate_realized_pnl", 0.0)) if isinstance(quality_rows, dict) else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Alpha Score (24h proxy)", f"{alpha_score:.4f}")
    c2.metric("Risk Decisions Blocked", str(blocked))
    c3.metric("Risk Decisions Allowed", str(allowed))
    c4.metric("Paper PnL Attribution", f"{paper_pnl:.4f}")

    st.subheader("Signal Review Status (Phase 49-50 lineage)")
    if signal_review:
        st.json(signal_review)
    else:
        st.info("No local signal review/readiness report found.")

    st.subheader("Paper Outcome Attribution")
    if quality_rows:
        st.json(quality_rows)
    else:
        st.info("No local outcome attribution report found.")

    st.subheader("Phase 56 Plan Status")
    if implementation:
        st.json(
            {
                "plan_id": implementation.get("plan_id"),
                "implementation_items": len(implementation.get("implementation_items", [])),
                "blocked_items": len(implementation.get("blocked_items", [])),
                "dry_run_only": implementation.get("dry_run_only"),
                "runtime_mutation_allowed": implementation.get("runtime_mutation_allowed"),
            }
        )
    else:
        st.info("No local Phase 56 plan report found.")

    st.error("No execution triggers available.")


if __name__ == "__main__":
    main()
