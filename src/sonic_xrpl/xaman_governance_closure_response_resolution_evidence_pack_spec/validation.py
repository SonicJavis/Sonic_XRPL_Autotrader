from __future__ import annotations

from sonic_xrpl.xaman_governance_closure_response_resolution_evidence_pack_spec.models import *


def build_xaman_governance_closure_response_resolution_evidence_pack_spec(
    row: XamanGovernanceClosureResponseResolutionEvidencePackFixtureInput,
) -> XamanGovernanceClosureResponseResolutionEvidencePackReport:
    errors: list[str] = []
    blockers: list[str] = []
    findings: list[EvidencePackFindingRecord] = []
    limits: list[EvidencePackLimitationRecord] = []

    def add(finding_id: str, category: str, severity: str, related: str, summary: str, block: bool = False) -> None:
        findings.append(EvidencePackFindingRecord(finding_id, category, related, severity, summary))
        limits.append(EvidencePackLimitationRecord(finding_id, category, related, severity, summary))
        (blockers if block else errors).append(finding_id)

    flag_map = (
        (row.missing_evidence_pack, "missing_evidence_pack", "MISSING_EVIDENCE_PACK", "HIGH"),
        (row.incomplete_evidence_pack, "incomplete_evidence_pack", "INCOMPLETE_EVIDENCE_PACK", "HIGH"),
        (row.missing_required_evidence, "missing_required_evidence", "MISSING_REQUIRED_EVIDENCE", "HIGH"),
        (row.stale_evidence_unresolved, "stale_evidence_unresolved", "STALE_EVIDENCE_UNRESOLVED", "MEDIUM"),
        (row.redacted_evidence_unresolved, "redacted_evidence_unresolved", "REDACTED_EVIDENCE_UNRESOLVED", "MEDIUM"),
        (row.reference_only_evidence_unresolved, "reference_only_evidence_unresolved", "REFERENCE_ONLY_EVIDENCE_UNRESOLVED", "HIGH"),
        (row.synthetic_only_evidence_unresolved, "synthetic_only_evidence_unresolved", "SYNTHETIC_ONLY_EVIDENCE_UNRESOLVED", "MEDIUM"),
        (row.unverified_evidence_unresolved, "unverified_evidence_unresolved", "UNVERIFIED_EVIDENCE_UNRESOLVED", "MEDIUM"),
        (row.missing_non_authorization_confirmation, "missing_non_authorization_confirmation", "MISSING_NON_AUTHORIZATION_CONFIRMATION", "HIGH"),
        (row.missing_owner, "missing_owner", "MISSING_OWNER", "HIGH"),
        (row.missing_reviewer, "missing_reviewer", "MISSING_REVIEWER", "HIGH"),
        (row.missing_follow_up_evidence_reference, "missing_follow_up_evidence_reference", "MISSING_FOLLOW_UP_EVIDENCE_REFERENCE", "MEDIUM"),
        (row.missing_evidence_sufficiency_mapping, "missing_evidence_sufficiency_mapping", "MISSING_EVIDENCE_SUFFICIENCY_MAPPING", "HIGH"),
        (row.unresolved_blocker_lacks_evidence, "unresolved_blocker_lacks_evidence", "UNRESOLVED_BLOCKER_LACKS_EVIDENCE", "HIGH"),
        (row.unresolved_limitation_lacks_evidence, "unresolved_limitation_lacks_evidence", "UNRESOLVED_LIMITATION_LACKS_EVIDENCE", "MEDIUM"),
        (row.dependency_audit_evidence_unresolved, "dependency_audit_evidence_unresolved", "DEPENDENCY_AUDIT_EVIDENCE_UNRESOLVED", "HIGH"),
        (row.safety_review_evidence_unresolved, "safety_review_evidence_unresolved", "SAFETY_REVIEW_EVIDENCE_UNRESOLVED", "HIGH"),
        (row.superseded_evidence_missing_replacement, "superseded_evidence_missing_replacement", "SUPERSEDED_EVIDENCE_MISSING_REPLACEMENT", "HIGH"),
        (row.rejected_evidence_unresolved, "rejected_evidence_unresolved", "REJECTED_EVIDENCE_UNRESOLVED", "HIGH"),
        (row.traceability_gap, "traceability_gap", "TRACEABILITY_GAP", "HIGH"),
    )
    for active, finding_id, category, severity in flag_map:
        if active:
            add(finding_id, category, severity, finding_id, finding_id.replace("_", " "))

    notices = set(row.non_authorization_notices)
    for notice in REQUIRED_NOTICES:
        if notice not in notices:
            add("missing_notice_" + notice.replace(" ", "_").replace("/", "_"), "MISSING_NON_AUTHORIZATION_CONFIRMATION", "HIGH", notice, "missing non-authorization confirmation")

    required_domains = {
        "CLOSURE_RESPONSE_RESOLUTION_REGISTER",
        "CLOSURE_RESPONSE_RESOLUTION_RECORDS",
        "FOLLOW_UP_EVIDENCE",
        "EVIDENCE_COMPLETENESS",
        "EVIDENCE_SUFFICIENCY_RESOLUTION",
        "UNRESOLVED_BLOCKERS",
        "UNRESOLVED_LIMITATIONS",
        "NON_AUTHORIZATION_CONFIRMATIONS",
        "OWNER_REVIEWER_MAPPING",
    }
    seen_domains = {record.evidence_pack_domain for record in row.evidence_pack_records}
    for domain in sorted(required_domains - seen_domains):
        add("missing_domain_" + domain.lower(), "MISSING_EVIDENCE_PACK_DOMAIN", "HIGH", domain, "missing required evidence pack domain")

    for record in row.evidence_pack_records:
        if not record.owner_role.strip():
            add("record_missing_owner_" + record.evidence_pack_id, "MISSING_OWNER", "HIGH", record.evidence_pack_id, "missing owner")
        if not record.reviewer_role.strip():
            add("record_missing_reviewer_" + record.evidence_pack_id, "MISSING_REVIEWER", "HIGH", record.evidence_pack_id, "missing reviewer")
        if not record.non_authorization_confirmation:
            add("record_missing_non_auth_" + record.evidence_pack_id, "MISSING_NON_AUTHORIZATION_CONFIRMATION", "HIGH", record.evidence_pack_id, "missing non-authorization confirmation")
        if not record.source_evidence_references:
            add("record_missing_source_evidence_" + record.evidence_pack_id, "MISSING_REQUIRED_EVIDENCE", "HIGH", record.evidence_pack_id, "missing required evidence")
        if not record.required_follow_up_evidence_references:
            add("record_missing_follow_up_" + record.evidence_pack_id, "MISSING_FOLLOW_UP_EVIDENCE_REFERENCE", "MEDIUM", record.evidence_pack_id, "missing follow-up evidence reference")
        if not record.evidence_sufficiency_status.strip():
            add("record_missing_sufficiency_" + record.evidence_pack_id, "MISSING_EVIDENCE_SUFFICIENCY_MAPPING", "HIGH", record.evidence_pack_id, "missing evidence sufficiency mapping")
        if record.evidence_status in {"EVIDENCE_BLOCKED"} or record.evidence_completeness_status == "BLOCKED" or record.evidence_sufficiency_status == "BLOCKED":
            add("record_blocked_" + record.evidence_pack_id, "EVIDENCE_PACK_BLOCKED", "CRITICAL", record.evidence_pack_id, "evidence pack blocked", True)
        elif record.evidence_status in {"EVIDENCE_MISSING", "EVIDENCE_STALE", "EVIDENCE_REDACTED", "EVIDENCE_REFERENCE_ONLY", "EVIDENCE_SYNTHETIC_ONLY", "EVIDENCE_UNVERIFIED"}:
            add("record_evidence_review_" + record.evidence_pack_id, record.evidence_status, record.severity or "MEDIUM", record.evidence_pack_id, "evidence requires review")
        if record.evidence_completeness_status in {"INCOMPLETE", "MISSING_REQUIRED_EVIDENCE", "SUPERSEDED", "REJECTED", "COMPLETENESS_REVIEW_REQUIRED"}:
            add("record_completeness_review_" + record.evidence_pack_id, record.evidence_completeness_status, record.severity or "MEDIUM", record.evidence_pack_id, "evidence completeness requires review")
        if record.evidence_sufficiency_status in {"INSUFFICIENT_EVIDENCE", "REVIEW_REQUIRED", "INCOMPLETE", "SUPERSEDED", "REJECTED"}:
            add("record_sufficiency_review_" + record.evidence_pack_id, record.evidence_sufficiency_status, record.severity or "MEDIUM", record.evidence_pack_id, "evidence sufficiency requires review")

    for active, finding_id, category in (
        (row.invalid_xaman_payload_approval_marker, "xaman_payload_approval_wording", "XAMAN_PAYLOAD_APPROVAL_WORDING"),
        (row.invalid_wallet_material_approval_marker, "wallet_material_approval_wording", "WALLET_MATERIAL_APPROVAL_WORDING"),
        (row.invalid_signing_submission_autofill_approval_marker, "signing_submission_autofill_approval_wording", "SIGNING_SUBMISSION_AUTOFILL_APPROVAL_WORDING"),
        (row.invalid_testnet_live_execution_approval_marker, "testnet_live_execution_approval_wording", "TESTNET_LIVE_EXECUTION_APPROVAL_WORDING"),
        (row.invalid_runtime_evidence_pack_service_marker, "runtime_closure_response_resolution_evidence_pack_service_marker", "RUNTIME_CLOSURE_RESPONSE_RESOLUTION_EVIDENCE_PACK_SERVICE_MARKER"),
        (row.invalid_download_service_marker, "download_service_marker", "DOWNLOAD_SERVICE_MARKER"),
        (row.invalid_api_ui_evidence_pack_route_marker, "api_ui_evidence_pack_route_marker", "API_UI_EVIDENCE_PACK_ROUTE_MARKER"),
        (row.invalid_safety_bypass_marker, "safety_bypass_marker", "SAFETY_BYPASS_MARKER"),
    ):
        if active:
            add(finding_id, category, "CRITICAL", finding_id, category, True)

    if blockers:
        classification = EVIDENCE_PACK_BLOCKED
    elif row.missing_evidence_pack:
        classification = EVIDENCE_PACK_INCOMPLETE
    elif errors:
        classification = EVIDENCE_PACK_REVIEW_REQUIRED if len(errors) < 4 else EVIDENCE_PACK_NOT_READY
    else:
        classification = EVIDENCE_PACK_SPEC_REVIEW_READY

    spec = XamanGovernanceClosureResponseResolutionEvidencePackSpec(
        "88",
        "Xaman governance closure response resolution evidence pack contract spec",
        row.evidence_pack_bundle_id,
        row.source_closure_response_resolution_register_id,
        row.source_closure_digest_response_bundle_id,
        row.deterministic_timestamp,
        EVIDENCE_PACK_DOMAINS,
        row.evidence_pack_records,
        tuple(findings),
        tuple(limits),
        REQUIRED_NOTICES,
    )
    return XamanGovernanceClosureResponseResolutionEvidencePackReport(row.fixture_id, spec, classification, tuple(errors + blockers), tuple(blockers))
