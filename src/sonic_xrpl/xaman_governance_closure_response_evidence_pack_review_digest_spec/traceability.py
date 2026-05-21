from __future__ import annotations

from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec.models import (
    XamanGovernanceClosureResponseEvidencePackReviewDigestReport,
)


def render_traceability_map(report: XamanGovernanceClosureResponseEvidencePackReviewDigestReport) -> dict:
    spec = report.spec
    sections = spec.review_digest_sections
    return {
        "review_digest_to_phase88_evidence_pack": spec.source_phase88_evidence_pack_bundle_id,
        "review_digest_to_phase87_closure_response_resolution_register": spec.source_closure_response_resolution_register_id,
        "review_digest_sections_to_phase88_evidence_pack_ids": {
            section.digest_section_id: section.related_phase88_evidence_pack_id for section in sections
        },
        "review_digest_to_phase86_closure_digest_response_ids": [section.related_phase86_closure_digest_response_id for section in sections if section.related_phase86_closure_digest_response_id],
        "review_digest_to_phase85_digest_ids": [section.related_phase85_digest_item_id for section in sections if section.related_phase85_digest_item_id],
        "review_digest_to_phase84_closure_evidence_ids": [section.related_phase84_closure_evidence_id for section in sections if section.related_phase84_closure_evidence_id],
        "review_digest_to_phase83_resolution_ids": [section.related_phase83_resolution_record_id for section in sections if section.related_phase83_resolution_record_id],
        "review_digest_to_phase82_response_ids": [section.related_phase82_response_record_id for section in sections if section.related_phase82_response_record_id],
        "review_digest_to_phase81_digest_ids": [section.related_phase81_digest_id for section in sections if section.related_phase81_digest_id],
        "review_digest_to_phase80_snapshot_ids": [section.related_phase80_snapshot_id for section in sections if section.related_phase80_snapshot_id],
        "review_digest_to_phase79_checklist_ids": [section.related_phase79_checklist_item_id for section in sections if section.related_phase79_checklist_item_id],
        "review_digest_to_phase78_approval_packet_ids": [section.related_phase78_approval_packet_id for section in sections if section.related_phase78_approval_packet_id],
        "review_digest_to_phase70_77_support_artifacts": sorted({item for section in sections for item in section.related_phase70_77_support_artifact_ids}),
        "digest_sections_to_counts": {
            section.digest_section_id: {
                "evidence_count": section.evidence_count,
                "complete_evidence_count": section.complete_evidence_count,
                "incomplete_evidence_count": section.incomplete_evidence_count,
                "sufficient_evidence_count": section.sufficient_evidence_count,
                "insufficient_evidence_count": section.insufficient_evidence_count,
                "blocker_count": section.blocker_count,
                "limitation_count": section.limitation_count,
            }
            for section in sections
        },
        "missing_digest_sections_fail_closed": bool(report.validation_errors),
        "missing_non_authorization_summary_fail_closed": any("non_authorization" in error for error in report.validation_errors),
    }
