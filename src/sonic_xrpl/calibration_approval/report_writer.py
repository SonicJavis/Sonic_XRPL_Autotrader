from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.calibration_approval.models import ApprovalLedger, jsonable


def _ledger_markdown(ledger: ApprovalLedger, proposal_source: str, review_source: str) -> str:
    lines = [
        "# Phase 55 Human Review Approval Ledger",
        "",
        f"Ledger ID: `{ledger.ledger_id}`",
        f"Generated at: `{ledger.generated_at}`",
        f"Proposal source: `{proposal_source}`",
        f"Review source: `{review_source}`",
        "",
        "## Safety",
        ledger.safety_summary,
        "No calibration changes are applied.",
        "Live execution remains blocked.",
        "",
        "## Decision Summary",
        *(f"- {decision}: {count}" for decision, count in ledger.counts_by_decision.items()),
        f"- change requests: {len(ledger.change_requests)}",
        "",
        "## Records",
        "| Record | Proposal | Decision | Reason |",
        "|---|---|---|---|",
        *(
            f"| `{record.approval_record_id}` | `{record.proposal_id}` | `{record.decision}` | {record.decision_reason or 'missing'} |"
            for record in ledger.records
        ),
        "",
        "## Limitations",
        *(f"- {item}" for item in (ledger.limitation_summary or ("none",))),
        "",
        "## Rollback",
        "Revert the Phase 55 merge commit. No runtime state is changed by this ledger.",
        "",
        "## Next Step",
        "Use requested change packets as input to a later reviewed implementation phase only.",
        "",
    ]
    return "\n".join(lines)


def _requests_markdown(ledger: ApprovalLedger) -> str:
    lines = [
        "# Phase 55 Calibration Change Requests",
        "",
        "Change requests are review artifacts only.",
        "apply_allowed=False",
        "runtime_mutation_allowed=False",
        "",
        "| Request | Proposal | Before | After | Delta | Status |",
        "|---|---|---:|---:|---:|---|",
        *(
            f"| `{item.change_request_id}` | `{item.proposal_id}` | {item.before_value} | {item.after_value} | {item.delta:+.2f} | `{item.status}` |"
            for item in ledger.change_requests
        ),
        "",
        "No calibration changes are applied.",
        "Live execution remains blocked.",
        "",
    ]
    return "\n".join(lines)


def write_approval_reports(
    ledger: ApprovalLedger,
    proposal_source: str,
    review_source: str,
    output_dir: str | Path = "reports/phase55",
) -> dict[str, str]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    ledger_json = target / "latest_calibration_approval_ledger.json"
    ledger_md = target / "latest_calibration_approval_ledger.md"
    requests_json = target / "latest_calibration_change_requests.json"
    requests_md = target / "latest_calibration_change_requests.md"
    ledger_payload = jsonable(ledger)
    ledger_payload["phase"] = "55"
    ledger_payload["proposal_pack_source"] = proposal_source
    ledger_payload["review_source"] = review_source
    ledger_json.write_text(json.dumps(ledger_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ledger_md.write_text(_ledger_markdown(ledger, proposal_source, review_source), encoding="utf-8")
    requests_json.write_text(
        json.dumps([jsonable(item) for item in ledger.change_requests], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    requests_md.write_text(_requests_markdown(ledger), encoding="utf-8")
    return {
        "approval_ledger_json": str(ledger_json),
        "approval_ledger_markdown": str(ledger_md),
        "change_requests_json": str(requests_json),
        "change_requests_markdown": str(requests_md),
    }
