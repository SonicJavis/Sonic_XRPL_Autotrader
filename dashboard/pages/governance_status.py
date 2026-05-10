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
    st.set_page_config(page_title="Governance Status", page_icon="S", layout="wide")
    st.title("Governance Status (Phase 53-56)")
    st.caption("Calibration queue, proposal/approval status, and implementation planning state.")

    p53 = _load_json(REPORTS / "phase53" / "calibration_readiness.json") or {}
    p54 = _load_json(REPORTS / "phase54" / "calibration_proposal_pack.json") or {}
    p55 = _load_json(REPORTS / "phase55" / "latest_calibration_approval_ledger.json") or {}
    p55_cr = _load_json(REPORTS / "phase55" / "latest_calibration_change_requests.json") or {}
    p56 = _load_json(REPORTS / "phase56" / "latest_calibration_implementation_plan.json") or {}

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Calibration Queue (P53)", str(p53.get("queued_recommendations", 0)))
    q2.metric("Proposal Records (P54)", str(len(p54.get("proposal_records", [])) if isinstance(p54, dict) else 0))
    q3.metric("Approval Records (P55)", str(len(p55.get("approval_records", [])) if isinstance(p55, dict) else 0))
    q4.metric("Phase 56 Items", str(len(p56.get("implementation_items", [])) if isinstance(p56, dict) else 0))

    st.subheader("Proposal / Approval / Change Requests")
    c1, c2, c3 = st.columns(3)
    c1.metric("Approved Requests", str(len(p55_cr.get("change_requests", [])) if isinstance(p55_cr, dict) else 0))
    c2.metric("Blocked Plan Items", str(len(p56.get("blocked_items", [])) if isinstance(p56, dict) else 0))
    c3.metric("Dry Run Only", "true" if p56.get("dry_run_only") else "false")

    st.subheader("Phase 56 Plan")
    if p56:
        st.json(
            {
                "plan_id": p56.get("plan_id"),
                "source_ledger_id": p56.get("source_ledger_id"),
                "source_change_request_count": p56.get("source_change_request_count"),
                "implementation_items": len(p56.get("implementation_items", [])),
                "blocked_items": len(p56.get("blocked_items", [])),
                "requires_human_implementation": p56.get("requires_human_implementation"),
            }
        )
    else:
        st.info("No Phase 56 plan report found.")


if __name__ == "__main__":
    main()
