from __future__ import annotations

from sonic_xrpl.xaman_governance_exception_waiver_register_spec.models import (
    BLOCKER_CATEGORIES,
    EXPIRY_REVOCATION_RULES,
    WAIVER_BLOCKED,
    WAIVER_DOMAINS,
    WAIVER_EXPIRED,
    WAIVER_NOT_READY,
    WAIVER_REVIEW_REQUIRED,
    WAIVER_REVOKED,
    WAIVER_ROLES,
    WAIVER_SEVERITIES,
    WAIVER_SPEC_REVIEW_READY,
    WAIVER_STATUSES,
    XamanGovernanceExceptionWaiverRegisterFixtureInput,
    XamanGovernanceExceptionWaiverRegisterReport,
    XamanGovernanceExceptionWaiverRegisterSpec,
)

UNSAFE_FLAGS = {
    "XAMAN_PAYLOAD_WAIVER_ATTEMPT",
    "WALLET_MATERIAL_WAIVER_ATTEMPT",
    "SIGNING_SUBMISSION_AUTOFILL_WAIVER_ATTEMPT",
    "TESTNET_LIVE_EXECUTION_WAIVER_ATTEMPT",
    "RUNTIME_MUTATION_WAIVER_ATTEMPT",
    "GUARD_WEAKENING_WAIVER_ATTEMPT",
    "SAFETY_BYPASS_MARKER",
}


def build_xaman_governance_exception_waiver_register_spec(
    row: XamanGovernanceExceptionWaiverRegisterFixtureInput,
) -> XamanGovernanceExceptionWaiverRegisterReport:
    errors: list[str] = []
    blockers: list[str] = []
    limitations: list[str] = [
        "accepted_for_spec_review_never_implies_execution_readiness",
        "waiver_register_is_non_executing",
    ]
    if not row.waiver_records:
        errors.append("missing_waiver_records")
    if not row.has_dependency_audit_resolution:
        errors.append("missing_dependency_audit_resolution")
    if not row.has_safety_scan_triage_resolution:
        errors.append("missing_safety_scan_triage_resolution")

    has_requested = False
    has_review_required = False
    has_expired = False
    has_revoked = False

    for rec in row.waiver_records:
        if rec.waiver_domain not in WAIVER_DOMAINS:
            errors.append(f"unknown_waiver_domain:{rec.waiver_id}")
        if rec.severity not in WAIVER_SEVERITIES:
            errors.append(f"unknown_waiver_severity:{rec.waiver_id}")
        if rec.requester_role not in WAIVER_ROLES:
            errors.append(f"unknown_requester_role:{rec.waiver_id}")
        if rec.reviewer_role and rec.reviewer_role not in WAIVER_ROLES:
            errors.append(f"unknown_reviewer_role:{rec.waiver_id}")
        if rec.current_status not in WAIVER_STATUSES:
            errors.append(f"unknown_status:{rec.waiver_id}")
        if not rec.reviewer_role.strip():
            errors.append(f"missing_reviewer:{rec.waiver_id}")
        if not rec.required_evidence_ids:
            errors.append(f"missing_required_evidence:{rec.waiver_id}")
        if set(rec.required_evidence_ids) - set(rec.supplied_evidence_ids):
            errors.append(f"missing_supplied_evidence:{rec.waiver_id}")
        if rec.stale_evidence_ids:
            errors.append(f"stale_waiver_evidence:{rec.waiver_id}")
        if not rec.compensating_control_references:
            errors.append(f"missing_compensating_control:{rec.waiver_id}")
        if not rec.expiry_policy and not rec.docs_only_spec_only:
            errors.append(f"missing_expiry_policy:{rec.waiver_id}")
        if rec.severity in {"CRITICAL", "BLOCKING"} and not rec.expiry_policy:
            errors.append(f"critical_missing_expiry_policy:{rec.waiver_id}")
        if not rec.revocation_policy:
            errors.append(f"missing_revocation_policy:{rec.waiver_id}")
        if rec.waiver_domain == "DEPENDENCY_RISK_WAIVER" and not rec.dependency_risk_classification:
            errors.append(f"missing_dependency_risk_classification:{rec.waiver_id}")
        if rec.current_status == "SUPERSEDED" and not rec.replacement_waiver_id:
            errors.append(f"missing_replacement_waiver_id:{rec.waiver_id}")
        if rec.current_status in {"REQUESTED", "EVIDENCE_PENDING"}:
            has_requested = True
        if rec.current_status in {"IN_REVIEW", "REJECTED", "SUPERSEDED"}:
            has_review_required = True
        if rec.current_status == "EXPIRED":
            has_expired = True
        if rec.current_status == "REVOKED":
            has_revoked = True
        if rec.current_status in {"REVOKED", "EXPIRED"} and rec.current_status == "ACCEPTED_FOR_SPEC_REVIEW":
            errors.append(f"invalid_terminal_acceptance:{rec.waiver_id}")
        unsafe = set(rec.safety_flags) & UNSAFE_FLAGS
        for flag in sorted(unsafe):
            blockers.append(f"{flag.lower()}:{rec.waiver_id}")

    marker_blockers = {
        row.invalid_xaman_payload_waiver_marker: "xaman_payload_waiver_attempt",
        row.invalid_wallet_material_waiver_marker: "wallet_material_waiver_attempt",
        row.invalid_signing_submission_autofill_waiver_marker: "signing_submission_autofill_waiver_attempt",
        row.invalid_testnet_live_execution_waiver_marker: "testnet_live_execution_waiver_attempt",
        row.invalid_runtime_mutation_waiver_marker: "runtime_mutation_waiver_attempt",
        row.invalid_guard_weakening_waiver_marker: "guard_weakening_waiver_attempt",
        row.invalid_safety_bypass_marker: "safety_bypass_marker",
    }
    for active, blocker in marker_blockers.items():
        if active:
            blockers.append(blocker)

    if blockers:
        readiness = WAIVER_BLOCKED
    elif has_revoked:
        readiness = WAIVER_REVOKED
    elif has_expired:
        readiness = WAIVER_EXPIRED
    elif errors:
        readiness = WAIVER_NOT_READY if len(errors) >= 4 else WAIVER_REVIEW_REQUIRED
    elif has_requested:
        readiness = WAIVER_NOT_READY
    elif has_review_required:
        readiness = WAIVER_REVIEW_REQUIRED
    else:
        readiness = WAIVER_SPEC_REVIEW_READY

    spec = XamanGovernanceExceptionWaiverRegisterSpec(
        phase="74",
        objective="Xaman governance exception waiver register contract spec",
        waiver_register_id=row.waiver_register_id,
        deterministic_timestamp=row.deterministic_timestamp,
        waiver_roles=WAIVER_ROLES,
        waiver_domains=WAIVER_DOMAINS,
        waiver_severities=WAIVER_SEVERITIES,
        waiver_statuses=WAIVER_STATUSES,
        expiry_revocation_rules=EXPIRY_REVOCATION_RULES,
        blocker_categories=BLOCKER_CATEGORIES,
        waiver_records=row.waiver_records,
        limitations=tuple(limitations),
    )
    return XamanGovernanceExceptionWaiverRegisterReport(
        fixture_id=row.fixture_id,
        spec=spec,
        readiness_classification=readiness,
        validation_errors=tuple(errors + blockers),
        blockers=tuple(blockers),
    )
