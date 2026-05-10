from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.calibration_implementation_plan.dry_run_patch import render_dry_run_preview
from sonic_xrpl.calibration_implementation_plan.models import CalibrationImplementationPlan, jsonable


def _plan_markdown(plan: CalibrationImplementationPlan, approval_source: str, requests_source: str) -> str:
    lines = [
        "# Phase 56 Approved Calibration Implementation Plan",
        "",
        f"Plan ID: `{plan.plan_id}`",
        f"Generated at: `{plan.created_at}`",
        f"Approval ledger source: `{approval_source}`",
        f"Change requests source: `{requests_source}`",
        "",
        "## Safety",
        plan.safety_summary,
        "",
        "## Summary",
        f"- implementation items: {len(plan.implementation_items)}",
        f"- blocked items: {len(plan.blocked_items)}",
        f"- source ledger id: `{plan.source_ledger_id}`",
        f"- source change requests: {plan.source_change_request_count}",
        "",
        "## Implementation Items",
        "| Item | Proposal | Target | Before | After | Delta |",
        "|---|---|---|---:|---:|---:|",
        *(
            f"| `{item.implementation_item_id}` | `{item.proposal_id}` | "
            f"`{item.target_namespace}.{item.target_parameter}` | "
            f"{item.current_value:.2f} | {item.proposed_value:.2f} | {item.exact_delta:+.2f} |"
            for item in plan.implementation_items
        ),
        "",
        "## Blocked Items",
        "| Change Request | Proposal | Reason | Required Next Action |",
        "|---|---|---|---|",
        *(
            f"| `{item.change_request_id}` | `{item.proposal_id}` | `{item.reason}` | {item.required_next_action} |"
            for item in plan.blocked_items
        ),
        "",
        "## Validation Commands",
        *(f"- `{cmd}`" for cmd in plan.validation_plan.required_commands),
        "",
        "## Rollback",
        *(f"- {step}" for step in plan.rollback_plan.rollback_steps),
        "",
        "## Limitations",
        *(f"- {text}" for text in plan.limitations),
        "",
    ]
    return "\n".join(lines)


def write_implementation_reports(
    plan: CalibrationImplementationPlan,
    approval_source: str,
    requests_source: str,
    output_dir: str | Path = "reports/phase56",
) -> dict[str, str]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    plan_json = target / "latest_calibration_implementation_plan.json"
    plan_md = target / "latest_calibration_implementation_plan.md"
    dry_run_md = target / "latest_calibration_dry_run_preview.md"

    payload = jsonable(plan)
    payload["approval_ledger_source"] = str(approval_source)
    payload["change_requests_source"] = str(requests_source)
    plan_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan_md.write_text(_plan_markdown(plan, str(approval_source), str(requests_source)), encoding="utf-8")
    dry_run_md.write_text(render_dry_run_preview(plan.implementation_items) + "\n", encoding="utf-8")

    return {
        "implementation_plan_json": str(plan_json),
        "implementation_plan_markdown": str(plan_md),
        "dry_run_preview_markdown": str(dry_run_md),
    }
