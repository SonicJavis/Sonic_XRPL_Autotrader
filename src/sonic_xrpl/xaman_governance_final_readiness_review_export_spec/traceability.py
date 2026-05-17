from __future__ import annotations
from sonic_xrpl.xaman_governance_final_readiness_review_export_spec.models import XamanGovernanceFinalReadinessReviewExportReport

def render_traceability_map(report: XamanGovernanceFinalReadinessReviewExportReport):
    return {
        "package_links":[{"export_package_id":report.spec.export_package_id,"manifest_id":report.spec.manifest.manifest_id}],
        "artifact_links":[{"export_artifact_id":a.export_artifact_id,"source_phase_number":a.source_phase_number,"source_artifact_type":a.source_artifact_type,"inclusion_status":a.inclusion_status,"redaction_status":a.redaction_status} for a in report.spec.export_artifacts],
        "summary_links":[{"summary_type":s.summary_type,"related_artifact_count":str(len(s.related_artifact_ids))} for s in report.spec.reviewer_summaries],
        "limitation_links":[{"limitation_id":l.limitation_id,"category":l.category,"related_artifact_id":l.related_artifact_id} for l in report.spec.limitation_register],
        "outcome_links":[{"export_readiness_classification":report.export_readiness_classification,"blocker_count":str(len(report.blockers)),"limitation_count":str(len(report.spec.limitation_register))}],
    }
