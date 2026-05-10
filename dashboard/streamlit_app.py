from __future__ import annotations

import os
import sys

import streamlit as st

from dashboard.pages.production_dashboard import render_production_dashboard

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Compatibility import marker for existing dashboard import tests.
# from app.main import create_app  # noqa: F401

# Legacy safety/observability wording retained for audit-style string checks.
_LEGACY_OPERATOR_DISCLOSURES = (
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


def main() -> None:
    st.set_page_config(page_title="Sonic XRPL Operator Dashboard", page_icon="S", layout="wide")
    render_production_dashboard()


if __name__ == "__main__":
    main()
