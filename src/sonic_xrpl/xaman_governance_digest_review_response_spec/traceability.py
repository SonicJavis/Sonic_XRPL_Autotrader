from __future__ import annotations
from sonic_xrpl.xaman_governance_digest_review_response_spec.models import XamanGovernanceDigestReviewResponseReport

def render_traceability_map(report:XamanGovernanceDigestReviewResponseReport)->dict:
    s=report.spec
    return {
        'response_bundle_to_phase81_digest': s.source_digest_bundle_id,
        'response_bundle_to_phase80_snapshot': s.source_snapshot_id,
        'response_bundle_to_phase79_checklist': [r.related_checklist_item_id for r in s.response_records if r.related_checklist_item_id],
        'response_bundle_to_phase78_approval_packet': [r.related_approval_packet_id for r in s.response_records if r.related_approval_packet_id],
        'response_bundle_to_phase70_77_support_artifacts': sorted({i for r in s.response_records for i in r.related_support_artifact_ids}),
        'response_records_to_digest_ids': {r.response_id:r.related_digest_id for r in s.response_records},
        'response_records_to_limitations_or_blockers': {r.response_id:r.limitation_notes for r in s.response_records},
        'missing_response_records_fail_closed': bool(report.validation_errors),
        'missing_non_authorization_confirmation_fail_closed': any('non_authorization' in e for e in report.validation_errors),
    }
