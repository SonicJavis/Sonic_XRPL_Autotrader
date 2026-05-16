from __future__ import annotations

from sonic_xrpl.xaman_governance_evidence_attestation_spec.models import (
    XamanGovernanceEvidenceAttestationReport,
)


def render_traceability_map(
    report: XamanGovernanceEvidenceAttestationReport,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for artifact in report.spec.evidence_artifacts:
        rows.append(
            {
                "evidence_id": artifact.evidence_id,
                "governance_domain": artifact.governance_domain,
                "linked_signoff_domain": artifact.linked_signoff_domain,
                "owner_role": artifact.owner_role,
                "provenance_label": artifact.provenance_label,
            }
        )
    return rows
