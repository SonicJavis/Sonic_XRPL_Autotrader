from __future__ import annotations

from sonic_xrpl.xaman_governance_signoff_matrix_spec.models import (
    XamanGovernanceSignoffReport,
)


def render_traceability_matrix(
    report: XamanGovernanceSignoffReport,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for req in report.spec.evidence_requirements:
        rows.append(
            {
                "requirement_key": req.key,
                "owner_role": req.owner_role,
                "severity_if_missing": req.blocker_severity_if_missing,
            }
        )
    return rows
