from __future__ import annotations

from sonic_xrpl.xaman_consent_evidence_pack_spec.models import XamanConsentEvidencePackSpecReport


def render_traceability_matrix(report: XamanConsentEvidencePackSpecReport) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for requirement in report.spec.evidence_requirements:
        rows.append(
            {
                "evidence_key": requirement.key,
                "evidence_label": requirement.label,
                "required": "true" if requirement.required else "false",
                "rationale": requirement.rationale,
            }
        )
    return rows
