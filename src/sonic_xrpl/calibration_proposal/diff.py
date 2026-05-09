from __future__ import annotations

from sonic_xrpl.calibration_proposal.models import CalibrationProposalPack


def render_proposal_diff(pack: CalibrationProposalPack) -> str:
    lines = [
        "Phase 54 calibration proposal diff",
        "proposed only - not applied",
        f"pack_id: {pack.pack_id}",
        f"paper_only: {str(pack.paper_only).lower()}",
        f"live_execution_allowed: {str(pack.live_execution_allowed).lower()}",
        f"auto_apply_allowed: {str(pack.auto_apply_allowed).lower()}",
        "",
    ]
    if not pack.proposals:
        lines.append("No exact proposal diffs are available.")
    for proposal in pack.proposals:
        parameter = proposal.parameter_ref
        lines.extend([
            f"{parameter.namespace}.{parameter.name}",
            f"  current:  {proposal.current_value}",
            f"  proposed: {proposal.proposed_value}",
            f"  delta:    {proposal.exact_delta:+.2f}",
            f"  range:    {parameter.allowed_range[0]}..{parameter.allowed_range[1]}",
            f"  status:   {proposal.status}",
            "",
        ])
    if pack.blocked_recommendations:
        lines.append("Blocked recommendations")
        for blocked in pack.blocked_recommendations:
            lines.append(f"  - {blocked.recommendation_id}: {blocked.reason}")
    lines.append("No settings were changed.")
    return "\n".join(lines)
