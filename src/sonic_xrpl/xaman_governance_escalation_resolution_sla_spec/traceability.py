from __future__ import annotations

from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec.models import (
    XamanGovernanceEscalationResolutionSLAReport,
)


def render_traceability_map(
    report: XamanGovernanceEscalationResolutionSLAReport,
) -> dict[str, list[dict[str, str]]]:
    sla_links = [
        {
            "sla_id": item.sla_id,
            "escalation_id": item.escalation_id,
            "workflow_step_id": item.workflow_step_id,
            "attestation_id": item.attestation_id,
            "signoff_domain": item.signoff_domain,
            "governance_domain": item.governance_domain,
        }
        for item in report.spec.sla_records
    ]
    resolution_links = [
        {
            "resolution_evidence_id": item.resolution_evidence_id,
            "escalation_id": item.escalation_id,
            "evidence_artifact_id": item.evidence_artifact_id,
        }
        for item in report.spec.resolution_evidence_records
    ]
    return {"sla_links": sla_links, "resolution_links": resolution_links}
