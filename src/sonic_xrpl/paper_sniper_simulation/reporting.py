from __future__ import annotations

import json

from sonic_xrpl.paper_sniper_simulation.models import PaperSniperSimulationReport, jsonable


def render_paper_sniper_report_payload(report: PaperSniperSimulationReport) -> dict:
    return jsonable(report)


def render_paper_sniper_report_json(report: PaperSniperSimulationReport) -> str:
    return json.dumps(render_paper_sniper_report_payload(report), indent=2, ensure_ascii=True, sort_keys=True)


def render_paper_sniper_report_markdown(report: PaperSniperSimulationReport) -> str:
    lines = [
        "# Phase 60 Paper-Only Sniper Simulation Report",
        "",
        "Paper-only simulation output. Not an order, not real execution, and not investment advice.",
        "",
        f"- Total candidates: {report.total_candidates}",
        f"- Simulated candidates: {report.simulated_candidates}",
        f"- Rejected candidates: {report.rejected_candidates}",
        f"- No-fill cases: {report.no_fill_candidates}",
        f"- Partial-fill cases: {report.partial_fill_candidates}",
        f"- Live execution allowed: `{report.live_execution_allowed}`",
        "",
    ]
    for row in report.results:
        lines.extend(
            [
                f"## {row.candidate_id}",
                "",
                f"- Intelligence verdict: `{row.intelligence_verdict}`",
                f"- Simulation decision: `{row.simulation_decision.value}`",
                f"- Fill assumption: `{row.fill_assumption.label.value}` ratio={row.fill_assumption.fill_ratio}",
                f"- Slippage assumption (bps): {row.fill_assumption.slippage_bps_assumption}",
                f"- Latency assumption (seconds): {row.fill_assumption.latency_seconds_assumption}",
                f"- Ledger-window assumption (seconds): {row.fill_assumption.ledger_window_seconds_assumption}",
                f"- Outcome window: `{row.outcome.outcome_window}`",
                f"- Assumed return (bps): {row.outcome.assumed_return_bps}",
                f"- Assumed PnL (XRP, paper-only): {row.outcome.assumed_pnl_xrp}",
                f"- Rejection reasons: {', '.join(row.rejection_reasons) or 'none'}",
                f"- Risk notes: {', '.join(row.risk_notes) or 'none'}",
                f"- Evidence limitations: {', '.join(row.limitations) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines)
