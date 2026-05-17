from __future__ import annotations

from sonic_xrpl.xaman_governance_final_readiness_bundle_spec.models import XamanGovernanceFinalReadinessBundleReport


def render_traceability_map(report: XamanGovernanceFinalReadinessBundleReport) -> dict[str, list[dict[str, str]]]:
    artifact_links = [
        {
            "artifact_id": item.artifact_id,
            "artifact_type": item.artifact_type,
            "phase_number": item.phase_number,
            "source_path": item.source_path,
        }
        for item in report.spec.artifact_references
    ]
    limitation_links = [
        {
            "limitation_id": item.limitation_id,
            "category": item.category,
            "related_artifact_id": item.related_artifact_id,
        }
        for item in report.spec.limitation_register
    ]
    outcome_links = [{
        "final_readiness_classification": report.final_readiness_classification,
        "supporting_artifact_count": str(len(report.spec.artifact_references)),
        "limitation_count": str(len(report.spec.limitation_register)),
    }]
    return {"artifact_links": artifact_links, "limitation_links": limitation_links, "outcome_links": outcome_links}
