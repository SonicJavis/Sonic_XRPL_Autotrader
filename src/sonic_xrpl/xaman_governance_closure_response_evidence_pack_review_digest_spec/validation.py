from __future__ import annotations

from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec.models import *


def build_xaman_governance_closure_response_evidence_pack_review_digest_spec(
    row: XamanGovernanceClosureResponseEvidencePackReviewDigestFixtureInput,
) -> XamanGovernanceClosureResponseEvidencePackReviewDigestReport:
    errors: list[str] = []
    blockers: list[str] = []
    findings: list[ReviewDigestFindingRecord] = []
    limits: list[ReviewDigestLimitationRecord] = []

    def add(finding_id: str, category: str, severity: str, related: str, summary: str, block: bool = False) -> None:
        findings.append(ReviewDigestFindingRecord(finding_id, category, related, severity, summary))
        limits.append(ReviewDigestLimitationRecord(finding_id, category, related, severity, summary))
        (blockers if block else errors).append(finding_id)

    flag_map = (
        (row.missing_evidence_pack, "missing_evidence_pack", "EVIDENCE_PACK_MISSING", "HIGH"),
        (row.incomplete_evidence_pack, "incomplete_evidence_pack", "EVIDENCE_PACK_INCOMPLETE", "HIGH"),
        (row.blocked_evidence_pack, "blocked_evidence_pack", "EVIDENCE_PACK_BLOCKED", "CRITICAL"),
        (row.missing_evidence_completeness_summary, "missing_evidence_completeness_summary", "MISSING_EVIDENCE_COMPLETENESS_SUMMARY", "HIGH"),
        (row.missing_evidence_sufficiency_summary, "missing_evidence_sufficiency_summary", "MISSING_EVIDENCE_SUFFICIENCY_SUMMARY", "HIGH"),
        (row.missing_owner_reviewer_summary, "missing_owner_reviewer_summary", "MISSING_OWNER_REVIEWER_SUMMARY", "HIGH"),
        (row.missing_non_authorization_summary, "missing_non_authorization_summary", "MISSING_NON_AUTHORIZATION_SUMMARY", "HIGH"),
        (row.hidden_unresolved_blocker, "hidden_unresolved_blocker", "UNRESOLVED_BLOCKER_SUMMARY_MISSING", "HIGH"),
        (row.hidden_unresolved_limitation, "hidden_unresolved_limitation", "UNRESOLVED_LIMITATION_SUMMARY_MISSING", "MEDIUM"),
        (row.stale_evidence_summary_gap, "stale_evidence_summary_gap", "STALE_EVIDENCE_SUMMARY_GAP", "MEDIUM"),
        (row.redacted_evidence_summary_gap, "redacted_evidence_summary_gap", "REDACTED_EVIDENCE_SUMMARY_GAP", "MEDIUM"),
        (row.reference_only_evidence_summary_gap, "reference_only_evidence_summary_gap", "REFERENCE_ONLY_EVIDENCE_SUMMARY_GAP", "HIGH"),
        (row.synthetic_only_evidence_summary_gap, "synthetic_only_evidence_summary_gap", "SYNTHETIC_ONLY_EVIDENCE_SUMMARY_GAP", "MEDIUM"),
        (row.unverified_evidence_summary_gap, "unverified_evidence_summary_gap", "UNVERIFIED_EVIDENCE_SUMMARY_GAP", "MEDIUM"),
        (row.dependency_audit_evidence_summary_gap, "dependency_audit_evidence_summary_gap", "MISSING_DEPENDENCY_AUDIT_EVIDENCE_SUMMARY", "HIGH"),
        (row.safety_review_evidence_summary_gap, "safety_review_evidence_summary_gap", "MISSING_SAFETY_REVIEW_EVIDENCE_SUMMARY", "HIGH"),
        (row.rejected_evidence_unresolved, "rejected_evidence_unresolved", "REJECTED_EVIDENCE_UNRESOLVED", "HIGH"),
        (row.superseded_evidence_missing_replacement, "superseded_evidence_missing_replacement", "SUPERSEDED_EVIDENCE_MISSING_REPLACEMENT", "HIGH"),
        (row.traceability_gap, "traceability_gap", "TRACEABILITY_SUMMARY_GAP", "HIGH"),
    )
    for active, finding_id, category, severity in flag_map:
        if active:
            add(finding_id, category, severity, finding_id, finding_id.replace("_", " "), category in {"EVIDENCE_PACK_BLOCKED"})

    notices = set(row.non_authorization_notices)
    for notice in REQUIRED_NOTICES:
        if notice not in notices:
            add("missing_notice_" + notice.replace(" ", "_").replace("/", "_"), "MISSING_NON_AUTHORIZATION_SUMMARY", "HIGH", notice, "missing non-authorization summary")

    required_domains = {
        "CLOSURE_RESPONSE_RESOLUTION_EVIDENCE_PACK",
        "EVIDENCE_PACK_RECORDS",
        "EVIDENCE_COMPLETENESS",
        "EVIDENCE_SUFFICIENCY",
        "UNRESOLVED_BLOCKERS",
        "UNRESOLVED_LIMITATIONS",
        "NON_AUTHORIZATION_CONFIRMATIONS",
        "OWNER_REVIEWER_MAPPING",
    }
    seen_domains = {section.digest_domain for section in row.review_digest_sections}
    for domain in sorted(required_domains - seen_domains):
        add("missing_domain_" + domain.lower(), "TRACEABILITY_SUMMARY_GAP", "HIGH", domain, "missing required review digest domain")

    for section in row.review_digest_sections:
        if not section.reviewer_visibility.strip():
            add("section_missing_reviewer_visibility_" + section.digest_section_id, "MISSING_OWNER_REVIEWER_SUMMARY", "HIGH", section.digest_section_id, "missing reviewer visibility")
        if section.evidence_count <= 0:
            add("section_missing_evidence_count_" + section.digest_section_id, "MISSING_EVIDENCE_PACK_SUMMARY", "HIGH", section.digest_section_id, "missing evidence pack summary")
        if section.complete_evidence_count + section.incomplete_evidence_count != section.evidence_count:
            add("section_completeness_mismatch_" + section.digest_section_id, "EVIDENCE_COMPLETENESS_REVIEW_REQUIRED", "HIGH", section.digest_section_id, "evidence completeness summary mismatch")
        if section.sufficient_evidence_count + section.insufficient_evidence_count != section.evidence_count:
            add("section_sufficiency_mismatch_" + section.digest_section_id, "EVIDENCE_SUFFICIENCY_GAP", "HIGH", section.digest_section_id, "evidence sufficiency summary mismatch")
        if section.blocker_count > 0 or section.digest_status == "EVIDENCE_PACK_DIGEST_BLOCKED":
            add("section_blocked_" + section.digest_section_id, "EVIDENCE_PACK_DIGEST_BLOCKED", "CRITICAL", section.digest_section_id, "review digest section blocked", True)
        elif section.incomplete_evidence_count > 0 or section.insufficient_evidence_count > 0 or section.digest_status in {"EVIDENCE_PACK_DIGEST_REVIEW_REQUIRED", "EVIDENCE_PACK_DIGEST_INCOMPLETE", "EVIDENCE_PACK_DIGEST_TRACEABILITY_GAP", "EVIDENCE_PACK_DIGEST_NON_AUTHORIZATION_MISSING"}:
            add("section_review_required_" + section.digest_section_id, section.digest_status or "EVIDENCE_PACK_DIGEST_REVIEW_REQUIRED", section.severity or "MEDIUM", section.digest_section_id, "review digest section requires review")

    for active, finding_id, category in (
        (row.invalid_xaman_payload_approval_marker, "xaman_payload_approval_wording", "XAMAN_PAYLOAD_APPROVAL_WORDING"),
        (row.invalid_wallet_material_approval_marker, "wallet_material_approval_wording", "WALLET_MATERIAL_APPROVAL_WORDING"),
        (row.invalid_signing_submission_autofill_approval_marker, "signing_submission_autofill_approval_wording", "SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING"),
        (row.invalid_testnet_live_execution_approval_marker, "testnet_live_execution_approval_wording", "TESTNET_LIVE_EXECUTION_APPROVAL_WORDING"),
        (row.invalid_runtime_review_digest_service_marker, "runtime_evidence_pack_review_digest_service_marker", "RUNTIME_EVIDENCE_PACK_REVIEW_DIGEST_SERVICE_MARKER"),
        (row.invalid_download_service_marker, "download_service_marker", "DOWNLOAD_SERVICE_MARKER"),
        (row.invalid_api_ui_evidence_pack_digest_route_marker, "api_ui_evidence_pack_digest_route_marker", "API_UI_EVIDENCE_PACK_DIGEST_ROUTE_MARKER"),
        (row.invalid_safety_bypass_marker, "safety_bypass_marker", "SAFETY_BYPASS_MARKER"),
    ):
        if active:
            add(finding_id, category, "CRITICAL", finding_id, category, True)

    if blockers:
        classification = EVIDENCE_PACK_DIGEST_BLOCKED
    elif row.missing_evidence_pack:
        classification = EVIDENCE_PACK_DIGEST_INCOMPLETE
    elif errors:
        classification = EVIDENCE_PACK_DIGEST_REVIEW_REQUIRED if len(errors) < 4 else EVIDENCE_PACK_DIGEST_NOT_READY
    else:
        classification = EVIDENCE_PACK_DIGEST_SPEC_REVIEW_READY

    spec = XamanGovernanceClosureResponseEvidencePackReviewDigestSpec(
        "89",
        "Xaman governance closure response evidence pack review digest contract spec",
        row.review_digest_bundle_id,
        row.source_phase88_evidence_pack_bundle_id,
        row.source_closure_response_resolution_register_id,
        row.deterministic_timestamp,
        REVIEW_DIGEST_DOMAINS,
        row.review_digest_sections,
        tuple(findings),
        tuple(limits),
        REQUIRED_NOTICES,
    )
    return XamanGovernanceClosureResponseEvidencePackReviewDigestReport(row.fixture_id, spec, classification, tuple(errors + blockers), tuple(blockers))
