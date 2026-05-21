from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec.models import (
    ReviewDigestSectionRecord,
    XamanGovernanceClosureResponseEvidencePackReviewDigestFixtureInput,
)


def _tuple(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in (value or []))


def _section(raw: dict[str, Any]) -> ReviewDigestSectionRecord:
    return ReviewDigestSectionRecord(
        digest_section_id=str(raw.get("digest_section_id", "")),
        digest_domain=str(raw.get("digest_domain", "")),
        related_phase88_evidence_pack_id=str(raw.get("related_phase88_evidence_pack_id", "")),
        related_phase87_closure_response_resolution_id=str(raw.get("related_phase87_closure_response_resolution_id", "")),
        related_phase86_closure_digest_response_id=str(raw.get("related_phase86_closure_digest_response_id", "")),
        related_phase85_digest_item_id=str(raw.get("related_phase85_digest_item_id", "")),
        related_phase84_closure_evidence_id=str(raw.get("related_phase84_closure_evidence_id", "")),
        related_phase83_resolution_record_id=str(raw.get("related_phase83_resolution_record_id", "")),
        related_phase82_response_record_id=str(raw.get("related_phase82_response_record_id", "")),
        related_phase81_digest_id=str(raw.get("related_phase81_digest_id", "")),
        related_phase80_snapshot_id=str(raw.get("related_phase80_snapshot_id", "")),
        related_phase79_checklist_item_id=str(raw.get("related_phase79_checklist_item_id", "")),
        related_phase78_approval_packet_id=str(raw.get("related_phase78_approval_packet_id", "")),
        related_phase70_77_support_artifact_ids=_tuple(raw.get("related_phase70_77_support_artifact_ids")),
        section_title=str(raw.get("section_title", "")),
        section_summary=str(raw.get("section_summary", "")),
        evidence_count=int(raw.get("evidence_count", 0)),
        complete_evidence_count=int(raw.get("complete_evidence_count", 0)),
        incomplete_evidence_count=int(raw.get("incomplete_evidence_count", 0)),
        sufficient_evidence_count=int(raw.get("sufficient_evidence_count", 0)),
        insufficient_evidence_count=int(raw.get("insufficient_evidence_count", 0)),
        blocker_count=int(raw.get("blocker_count", 0)),
        limitation_count=int(raw.get("limitation_count", 0)),
        reviewer_visibility=str(raw.get("reviewer_visibility", "")),
        digest_status=str(raw.get("digest_status", "")),
        severity=str(raw.get("severity", "")),
        limitation_notes=str(raw.get("limitation_notes", "")),
        safety_flags=_tuple(raw.get("safety_flags")),
    )


def load_xaman_governance_closure_response_evidence_pack_review_digest_fixture(
    path: str | Path,
) -> XamanGovernanceClosureResponseEvidencePackReviewDigestFixtureInput:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    sections = tuple(_section(item) for item in data.get("review_digest_sections", []))
    flags = {key: bool(data.get(key, False)) for key in (
        "missing_evidence_pack",
        "incomplete_evidence_pack",
        "blocked_evidence_pack",
        "missing_evidence_completeness_summary",
        "missing_evidence_sufficiency_summary",
        "missing_owner_reviewer_summary",
        "missing_non_authorization_summary",
        "hidden_unresolved_blocker",
        "hidden_unresolved_limitation",
        "stale_evidence_summary_gap",
        "redacted_evidence_summary_gap",
        "reference_only_evidence_summary_gap",
        "synthetic_only_evidence_summary_gap",
        "unverified_evidence_summary_gap",
        "dependency_audit_evidence_summary_gap",
        "safety_review_evidence_summary_gap",
        "rejected_evidence_unresolved",
        "superseded_evidence_missing_replacement",
        "traceability_gap",
        "invalid_xaman_payload_approval_marker",
        "invalid_wallet_material_approval_marker",
        "invalid_signing_submission_autofill_approval_marker",
        "invalid_testnet_live_execution_approval_marker",
        "invalid_runtime_review_digest_service_marker",
        "invalid_download_service_marker",
        "invalid_api_ui_evidence_pack_digest_route_marker",
        "invalid_safety_bypass_marker",
    )}
    return XamanGovernanceClosureResponseEvidencePackReviewDigestFixtureInput(
        fixture_id=str(data["fixture_id"]),
        review_digest_bundle_id=str(data["review_digest_bundle_id"]),
        source_phase88_evidence_pack_bundle_id=str(data["source_phase88_evidence_pack_bundle_id"]),
        source_closure_response_resolution_register_id=str(data["source_closure_response_resolution_register_id"]),
        deterministic_timestamp=str(data["deterministic_timestamp"]),
        evidence_pack_classification=str(data.get("evidence_pack_classification", "EVIDENCE_PACK_SPEC_REVIEW_READY")),
        closure_response_resolution_classification=str(data.get("closure_response_resolution_classification", "CLOSURE_RESPONSE_RESOLUTION_REGISTER_SPEC_REVIEW_READY")),
        review_digest_sections=sections,
        non_authorization_notices=_tuple(data.get("non_authorization_notices")),
        **flags,
    )
