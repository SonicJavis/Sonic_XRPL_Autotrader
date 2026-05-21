from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec.models import (
    EvidencePackRecord,
    XamanGovernanceClosureResponseResolutionEvidencePackFixtureInput,
)


def _load_record(row: dict) -> EvidencePackRecord:
    return EvidencePackRecord(
        row["evidence_pack_id"],
        row["evidence_pack_domain"],
        row.get("related_phase87_closure_response_resolution_id", ""),
        row.get("related_phase86_closure_digest_response_id", ""),
        row.get("related_phase85_digest_item_id", ""),
        row.get("related_phase84_closure_evidence_id", ""),
        row.get("related_phase83_resolution_record_id", ""),
        row.get("related_phase82_response_record_id", ""),
        row.get("related_phase81_digest_id", ""),
        row.get("related_phase80_snapshot_id", ""),
        row.get("related_phase79_checklist_item_id", ""),
        row.get("related_phase78_approval_packet_id", ""),
        tuple(row.get("related_phase70_77_support_artifact_ids", [])),
        row.get("owner_role", ""),
        row.get("reviewer_role", ""),
        row.get("evidence_category", "DOCUMENTATION_EVIDENCE"),
        row.get("evidence_status", "EVIDENCE_UNVERIFIED"),
        row.get("evidence_completeness_status", "COMPLETENESS_REVIEW_REQUIRED"),
        row.get("evidence_sufficiency_status", "REVIEW_REQUIRED"),
        row.get("evidence_summary", ""),
        tuple(row.get("source_evidence_references", [])),
        tuple(row.get("required_follow_up_evidence_references", [])),
        tuple(row.get("unresolved_blocker_references", [])),
        tuple(row.get("unresolved_limitation_references", [])),
        bool(row.get("non_authorization_confirmation", False)),
        row.get("evidence_pack_limitation_notes", ""),
        row.get("severity", "MEDIUM"),
        tuple(row.get("safety_flags", [])),
    )


def load_xaman_governance_closure_response_resolution_evidence_pack_fixture(
    path: str | Path,
) -> XamanGovernanceClosureResponseResolutionEvidencePackFixtureInput:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    records = tuple(_load_record(item) for item in data.get("evidence_pack_records", []))

    return XamanGovernanceClosureResponseResolutionEvidencePackFixtureInput(
        data["fixture_id"],
        data["evidence_pack_bundle_id"],
        data["source_closure_response_resolution_register_id"],
        data["source_closure_digest_response_bundle_id"],
        data.get("deterministic_timestamp", "1970-01-01T00:00:00Z"),
        data.get("closure_response_resolution_classification", "CLOSURE_RESPONSE_RESOLUTION_REGISTER_REVIEW_REQUIRED"),
        data.get("closure_digest_response_classification", "CLOSURE_DIGEST_RESPONSE_REVIEW_REQUIRED"),
        records,
        tuple(data.get("non_authorization_notices", [])),
        bool(data.get("missing_evidence_pack", False)),
        bool(data.get("incomplete_evidence_pack", False)),
        bool(data.get("missing_required_evidence", False)),
        bool(data.get("stale_evidence_unresolved", False)),
        bool(data.get("redacted_evidence_unresolved", False)),
        bool(data.get("reference_only_evidence_unresolved", False)),
        bool(data.get("synthetic_only_evidence_unresolved", False)),
        bool(data.get("unverified_evidence_unresolved", False)),
        bool(data.get("missing_non_authorization_confirmation", False)),
        bool(data.get("missing_owner", False)),
        bool(data.get("missing_reviewer", False)),
        bool(data.get("missing_follow_up_evidence_reference", False)),
        bool(data.get("missing_evidence_sufficiency_mapping", False)),
        bool(data.get("unresolved_blocker_lacks_evidence", False)),
        bool(data.get("unresolved_limitation_lacks_evidence", False)),
        bool(data.get("dependency_audit_evidence_unresolved", False)),
        bool(data.get("safety_review_evidence_unresolved", False)),
        bool(data.get("superseded_evidence_missing_replacement", False)),
        bool(data.get("rejected_evidence_unresolved", False)),
        bool(data.get("traceability_gap", False)),
        bool(data.get("invalid_xaman_payload_approval_marker", False)),
        bool(data.get("invalid_wallet_material_approval_marker", False)),
        bool(data.get("invalid_signing_submission_autofill_approval_marker", False)),
        bool(data.get("invalid_testnet_live_execution_approval_marker", False)),
        bool(data.get("invalid_runtime_evidence_pack_service_marker", False)),
        bool(data.get("invalid_download_service_marker", False)),
        bool(data.get("invalid_api_ui_evidence_pack_route_marker", False)),
        bool(data.get("invalid_safety_bypass_marker", False)),
    )
