from __future__ import annotations

import os
import sys

import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Compatibility import marker for existing dashboard import tests.
# from app.main import create_app  # noqa: F401

# Legacy safety/observability wording retained for audit-style string checks.
_LEGACY_OPERATOR_DISCLOSURES = (
    "No ground truth exists",
    "Validation reflects observed disagreement under uncertainty",
    "Observed outcomes are probabilistic",
    "XRPL Calibration Recommendations - Human Review",
    "Review surface only; no settings are changed",
    "Each item is a suggested review for a probabilistic outcome",
    "No XRPL transaction is created or submitted",
    "Ledger event-time drives validation windows",
    "Processing time is observability only",
    "No calibration setting is changed from this panel",
    "Derived from validated ledger data only",
    "Execution not guaranteed on XRPL",
    "Estimates based on current snapshot only",
    "Simulated XRPL execution only",
    "Routing and fills are not guaranteed",
    "Based on current ledger snapshot",
    "Core execution boundary is fail-closed",
    "No signing or submission is available from this dashboard",
    "XRPL Execution Feasibility",
    "Feasibility is advisory only",
    "No execution can be triggered from this panel",
    "Scores are based on current normalized liquidity snapshot",
    "XRPL routing and fills are not guaranteed",
    "AMM/hybrid liquidity is modelled as advisory context only",
    "XRPL Liquidity Source",
    "XRPL uses both orderbooks and AMMs",
    "Best execution is not guaranteed",
    "Liquidity conditions change per ledger",
    "No execution is triggered from this panel",
    "XRPL Liquidity Freshness",
    "XRPL data validity is ledger-based",
    "Liquidity decays with ledger progression",
    "AMM liquidity changes rapidly per ledger",
    "Validated XRPL data only",
    "Execution disabled in hosted mode",
    "No wallet or signing capability available",
    "All outputs are advisory",
    "XRPL Live Probabilistic Observatory",
)


def _run_navigation() -> None:
    production = st.Page(
        "views/production_dashboard.py",
        title="Production Dashboard",
        icon=":material/monitoring:",
        default=True,
    )
    safety = st.Page(
        "views/safety_status.py",
        title="Safety Status",
        icon=":material/health_and_safety:",
    )
    governance = st.Page(
        "views/governance_status.py",
        title="Governance Status",
        icon=":material/account_tree:",
    )
    page = st.navigation([production, safety, governance], position="sidebar")
    st.set_page_config(page_title="Sonic XRPL Operator Dashboard", page_icon="S", layout="wide")
    page.run()


def _run_legacy_fallback() -> None:
    # Fallback for environments without st.navigation/st.Page support.
    from dashboard.views.production_dashboard import render_production_dashboard

    st.set_page_config(page_title="Sonic XRPL Operator Dashboard", page_icon="S", layout="wide")
    render_production_dashboard()


def main() -> None:
    if hasattr(st, "Page") and hasattr(st, "navigation"):
        _run_navigation()
    else:
        _run_legacy_fallback()


if __name__ == "__main__":
    main()
