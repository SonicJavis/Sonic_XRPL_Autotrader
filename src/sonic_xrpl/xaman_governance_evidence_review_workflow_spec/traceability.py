from __future__ import annotations

from sonic_xrpl.xaman_governance_evidence_review_workflow_spec.models import (
    XamanGovernanceEvidenceReviewWorkflowReport,
)


def render_traceability_map(
    report: XamanGovernanceEvidenceReviewWorkflowReport,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for step in report.spec.steps:
        rows.append(
            {
                "step_id": step.step_id,
                "stage_type": step.stage_type,
                "role": step.role,
                "linked_evidence_id": step.linked_evidence_id,
                "linked_attestation_id": step.linked_attestation_id,
            }
        )
    return rows
