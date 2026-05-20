from __future__ import annotations
from sonic_xrpl.xaman_governance_response_resolution_register_spec.models import XamanGovernanceResponseResolutionRegisterReport

def render_traceability_map(report:XamanGovernanceResponseResolutionRegisterReport)->dict:
    s=report.spec
    return {
        'resolution_register_to_phase82_response_bundle': s.source_response_bundle_id,
        'resolution_register_to_phase81_digest_bundle': s.source_digest_bundle_id,
        'resolution_register_to_phase80_snapshot_ids': [r.related_snapshot_id for r in s.resolution_records if r.related_snapshot_id],
        'resolution_register_to_phase79_checklist_ids': [r.related_checklist_item_id for r in s.resolution_records if r.related_checklist_item_id],
        'resolution_register_to_phase78_approval_packet_ids': [r.related_approval_packet_id for r in s.resolution_records if r.related_approval_packet_id],
        'resolution_register_to_phase70_77_support_artifacts': sorted({i for r in s.resolution_records for i in r.related_support_artifact_ids}),
        'resolution_records_to_response_ids': {r.resolution_id:r.related_response_record_id for r in s.resolution_records},
        'resolution_records_to_blockers_limitations': {r.resolution_id:{'blockers':list(r.unresolved_blocker_references),'limitations':list(r.unresolved_limitation_references)} for r in s.resolution_records},
        'missing_resolution_records_fail_closed': bool(report.validation_errors),
        'missing_non_authorization_confirmation_fail_closed': any('non_authorization' in e for e in report.validation_errors),
    }
