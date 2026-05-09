from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.calibration_proposal.diff import render_proposal_diff
from sonic_xrpl.calibration_proposal.models import CalibrationProposalPack, jsonable


def _markdown(pack: CalibrationProposalPack) -> str:
    lines = [
        "# Phase 54 Human-Reviewed Calibration Proposal Pack",
        "",
        f"Pack ID: `{pack.pack_id}`",
        f"Phase: `{pack.phase}`",
        f"Generated at: `{pack.created_at}`",
        f"Paper only: `{str(pack.paper_only).lower()}`",
        f"Live execution allowed: `{str(pack.live_execution_allowed).lower()}`",
        f"Auto apply allowed: `{str(pack.auto_apply_allowed).lower()}`",
        "",
        "## Safety Statement",
        pack.safety_statement,
        "",
        "## Source Input Summary",
        *(f"- {key}: {value}" for key, value in pack.input_summary.items()),
        "",
        "## Proposal Summary",
        "| Parameter | Direction | Current | Proposed | Delta | Confidence |",
        "|---|---:|---:|---:|---:|---:|",
        *(
            f"| `{item.parameter_ref.name}` | `{item.direction}` | {item.current_value} | {item.proposed_value} | {item.exact_delta:+.2f} | {item.confidence} |"
            for item in pack.proposals
        ),
        "",
        "## Blocked Proposals",
        "| Recommendation | Reason | Required Next Evidence |",
        "|---|---|---|",
        *(
            f"| `{item.recommendation_id}` | {item.reason} | {'; '.join(item.required_next_evidence)} |"
            for item in pack.blocked_recommendations
        ),
        "",
        "## Before After Diff",
        "```text",
        render_proposal_diff(pack),
        "```",
        "",
        "## Evidence References",
        *(
            f"- `{evidence}`"
            for proposal in pack.proposals
            for evidence in proposal.supporting_evidence_ids
        ),
        "",
        "## Risk Notes",
        f"- Risk level: {pack.risk_summary.risk_level}",
        f"- Evidence quality: {pack.risk_summary.evidence_quality}",
        f"- Synthetic ratio: {pack.risk_summary.synthetic_ratio}",
        f"- Missing observations: {pack.risk_summary.missing_observation_count}",
        f"- Invalid observations: {pack.risk_summary.invalid_observation_count}",
        *(f"- {reason}" for reason in pack.risk_summary.reasons),
        "",
        "## Human Review Checklist",
        "| Required | Status | Question | Evidence |",
        "|---:|---|---|---|",
        *(
            f"| {str(item.required).lower()} | `{item.status}` | {item.question} | `{item.evidence_reference}` |"
            for item in pack.review_checklist
        ),
        "",
        "## Approval Requirements",
        *(f"- {item}" for item in pack.approval_requirements),
        "",
        "## Rollback Notes",
        "Rollback is a normal revert of the Phase 54 merge commit. No database migration, external service setup, live config, or credential material is introduced.",
        "",
        "## Remaining Limitations",
        *(f"- {item}" for item in (pack.limitations or ("No additional limitations beyond source evidence quality.",))),
        "",
        "No settings were changed.",
        "Live execution remains blocked.",
        "",
    ]
    return "\n".join(lines)


def write_calibration_proposal_report(
    pack: CalibrationProposalPack,
    output_dir: str | Path = "reports/phase54",
) -> dict[str, str]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "calibration_proposal_pack.json"
    md_path = target / "calibration_proposal_pack.md"
    payload = jsonable(pack)
    payload["generated_at"] = pack.created_at
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_markdown(pack), encoding="utf-8")
    return {
        "proposal_json": str(json_path),
        "proposal_markdown": str(md_path),
    }
