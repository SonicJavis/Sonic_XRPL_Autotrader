from __future__ import annotations

from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec.models import (
    XamanGovernanceClosureResponseResolutionEvidencePackReport,
)


def render_traceability_map(report: XamanGovernanceClosureResponseResolutionEvidencePackReport) -> dict:
    spec = report.spec
    records = spec.evidence_pack_records
    return {
        "evidence_pack_to_phase87_closure_response_resolution_register": spec.source_closure_response_resolution_register_id,
        "evidence_pack_to_phase86_closure_digest_response": spec.source_closure_digest_response_bundle_id,
        "evidence_pack_records_to_phase87_resolution_ids": {
            record.evidence_pack_id: record.related_phase87_closure_response_resolution_id for record in records
        },
        "evidence_pack_to_phase85_digest_ids": [record.related_phase85_digest_item_id for record in records if record.related_phase85_digest_item_id],
        "evidence_pack_to_phase84_closure_evidence_ids": [record.related_phase84_closure_evidence_id for record in records if record.related_phase84_closure_evidence_id],
        "evidence_pack_to_phase83_resolution_ids": [record.related_phase83_resolution_record_id for record in records if record.related_phase83_resolution_record_id],
        "evidence_pack_to_phase82_response_ids": [record.related_phase82_response_record_id for record in records if record.related_phase82_response_record_id],
        "evidence_pack_to_phase81_digest_ids": [record.related_phase81_digest_id for record in records if record.related_phase81_digest_id],
        "evidence_pack_to_phase80_snapshot_ids": [record.related_phase80_snapshot_id for record in records if record.related_phase80_snapshot_id],
        "evidence_pack_to_phase79_checklist_ids": [record.related_phase79_checklist_item_id for record in records if record.related_phase79_checklist_item_id],
        "evidence_pack_to_phase78_approval_packet_ids": [record.related_phase78_approval_packet_id for record in records if record.related_phase78_approval_packet_id],
        "evidence_pack_to_phase70_77_support_artifacts": sorted({item for record in records for item in record.related_phase70_77_support_artifact_ids}),
        "evidence_pack_records_to_blockers_limitations": {
            record.evidence_pack_id: {
                "blockers": list(record.unresolved_blocker_references),
                "limitations": list(record.unresolved_limitation_references),
                "source_evidence": list(record.source_evidence_references),
            }
            for record in records
        },
        "missing_evidence_pack_records_fail_closed": bool(report.validation_errors),
        "missing_non_authorization_confirmation_fail_closed": any("non_authorization" in error for error in report.validation_errors),
    }
