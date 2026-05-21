from __future__ import annotations
import json
from pathlib import Path

from sonic_xrpl.xaman_governance_closure_response_resolution_register_spec.models import (
    ClosureResponseResolutionRecord,
    XamanGovernanceClosureResponseResolutionRegisterFixtureInput,
)


def _load_response(row: dict) -> ClosureResponseResolutionRecord:
    return ClosureResponseResolutionRecord(
        row['closure_response_resolution_id'],
        row['resolution_domain'],
        row.get('related_phase85_digest_item_id', ''),
        row.get('related_phase84_closure_evidence_id', ''),
        row.get('related_phase83_resolution_record_id', ''),
        row.get('related_phase82_response_record_id', ''),
        row.get('related_phase81_digest_id', ''),
        row.get('related_phase80_snapshot_id', ''),
        row.get('related_phase79_checklist_item_id', ''),
        row.get('related_phase78_approval_packet_id', ''),
        tuple(row.get('related_phase70_77_support_artifact_ids', [])),
        row.get('reviewer_role', ''),
        row.get('resolution_category', 'RESOLUTION_REVIEW_REQUIRED'),
        row.get('resolution_status', 'CLOSURE_RESPONSE_RESOLUTION_NOT_STARTED'),
        row.get('resolution_summary', ''),
        tuple(row.get('required_follow_up_evidence_references', [])),
        row.get('evidence_sufficiency_response', ''),
        tuple(row.get('unresolved_blocker_references', [])),
        tuple(row.get('unresolved_limitation_references', [])),
        bool(row.get('non_authorization_confirmation', False)),
        row.get('closure_condition', row.get('resolution_intent', 'NO_RUNTIME_ACTION')),
        row.get('deferral_reason', ''),
        row.get('rejection_reason', ''),
        row.get('superseded_by_resolution_id', ''),
        row.get('severity', 'MEDIUM'),
        row.get('limitation_notes', ''),
        tuple(row.get('safety_flags', [])),
    )


def load_xaman_governance_closure_response_resolution_register_fixture(
    path: str | Path,
) -> XamanGovernanceClosureResponseResolutionRegisterFixtureInput:
    p = Path(path)
    data = json.loads(p.read_text(encoding='utf-8-sig'))
    records = tuple(_load_response(i) for i in data.get('resolution_records', []))
    source_closure_digest_response_bundle_id = data.get(
        'source_closure_digest_response_bundle_id',
        data.get('source_closure_response_resolution_register_id', ''),
    )

    return XamanGovernanceClosureResponseResolutionRegisterFixtureInput(
        data['fixture_id'],
        data['closure_response_resolution_register_id'],
        source_closure_digest_response_bundle_id,
        data['source_closure_bundle_id'],
        data.get('deterministic_timestamp', '1970-01-01T00:00:00Z'),
        data.get('closure_digest_classification', 'CLOSURE_DIGEST_REVIEW_REQUIRED'),
        data.get('closure_classification', 'CLOSURE_BUNDLE_REVIEW_REQUIRED'),
        records,
        tuple(data.get('non_authorization_notices', [])),
        bool(data.get('missing_closure_digest_response', False)),
        bool(data.get('incomplete_closure_digest_response', False)),
        bool(data.get('rejected_closure_digest_response_unresolved', False)),
        bool(data.get('deferred_blocker_without_limitation', False)),
        bool(data.get('superseded_response_missing_replacement', False)),
        bool(data.get('missing_non_authorization_confirmation', False)),
        bool(data.get('missing_reviewer_response', False)),
        bool(data.get('missing_follow_up_evidence_reference', False)),
        bool(data.get('missing_evidence_sufficiency_response', False)),
        bool(data.get('unresolved_blocker_lacks_response', False)),
        bool(data.get('unresolved_limitation_lacks_response', False)),
        bool(data.get('stale_closure_evidence_response_unresolved', False)),
        bool(data.get('redacted_closure_evidence_response_unresolved', False)),
        bool(data.get('reference_only_closure_evidence_response_unresolved', False)),
        bool(data.get('synthetic_only_closure_evidence_response_unresolved', False)),
        bool(data.get('dependency_audit_response_unresolved', False)),
        bool(data.get('safety_review_response_unresolved', False)),
        bool(data.get('traceability_gap', False)),
        bool(data.get('invalid_xaman_payload_approval_marker', False)),
        bool(data.get('invalid_wallet_material_approval_marker', False)),
        bool(data.get('invalid_signing_submission_autofill_approval_marker', False)),
        bool(data.get('invalid_testnet_live_execution_approval_marker', False)),
        bool(data.get('invalid_runtime_closure_digest_response_service_marker', False)),
        bool(data.get('invalid_download_service_marker', False)),
        bool(data.get('invalid_api_ui_closure_digest_response_route_marker', False)),
        bool(data.get('invalid_safety_bypass_marker', False)),
    )
