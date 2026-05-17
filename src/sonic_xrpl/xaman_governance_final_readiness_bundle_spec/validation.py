from __future__ import annotations

from sonic_xrpl.xaman_governance_final_readiness_bundle_spec.models import (
    COMPLETENESS_CHECKS,
    FINAL_BLOCKED,
    FINAL_BUNDLE_DOMAINS,
    FINAL_INCOMPLETE,
    FINAL_NOT_READY,
    FINAL_REVIEW_REQUIRED,
    FINAL_SPEC_REVIEW_READY,
    LIMITATION_CATEGORIES,
    MANDATORY_ARTIFACT_TYPES,
    LimitationRecord,
    XamanGovernanceFinalReadinessBundleFixtureInput,
    XamanGovernanceFinalReadinessBundleReport,
    XamanGovernanceFinalReadinessBundleSpec,
)


def build_xaman_governance_final_readiness_bundle_spec(
    row: XamanGovernanceFinalReadinessBundleFixtureInput,
) -> XamanGovernanceFinalReadinessBundleReport:
    errors: list[str] = []
    blockers: list[str] = []
    limitations: list[LimitationRecord] = []

    artifact_types = {item.artifact_type for item in row.artifact_references}
    missing_types = set(MANDATORY_ARTIFACT_TYPES) - artifact_types
    for artifact_type in sorted(missing_types):
        errors.append(f"missing_required_artifact:{artifact_type}")
        limitations.append(LimitationRecord(f"lim-{artifact_type.lower()}", "MISSING_REQUIRED_ARTIFACT", artifact_type, "HIGH", "mandatory artifact absent"))

    phase_presence = {
        "phase70_report_present": row.phase70_present,
        "phase71_report_present": row.phase71_present,
        "phase72_report_present": row.phase72_present,
        "phase73_report_present": row.phase73_present,
        "phase74_report_present": row.phase74_present,
    }
    for check, present in phase_presence.items():
        if not present:
            errors.append(check.replace("_present", "_missing"))
            limitations.append(LimitationRecord(f"lim-{check}", "MISSING_REQUIRED_ARTIFACT", check, "HIGH", "mandatory phase artifact missing"))

    if row.unresolved_safety_review:
        errors.append("unresolved_safety_review")
        limitations.append(LimitationRecord("lim-safety-review", "UNRESOLVED_SAFETY_REVIEW", "SAFETY_SCAN_SUMMARY", "HIGH", "safety review unresolved"))
    if row.unresolved_dependency_risk:
        errors.append("unresolved_dependency_risk")
        limitations.append(LimitationRecord("lim-dependency-risk", "UNRESOLVED_DEPENDENCY_AUDIT_RISK", "DEPENDENCY_AUDIT_SUMMARY", "HIGH", "dependency audit risk unresolved"))
    if row.expired_waiver:
        errors.append("expired_waiver")
        limitations.append(LimitationRecord("lim-expired-waiver", "EXPIRED_WAIVER", "PHASE74_WAIVER_REGISTER_REPORT", "HIGH", "expired waiver present"))
    if row.revoked_waiver:
        errors.append("revoked_waiver")
        limitations.append(LimitationRecord("lim-revoked-waiver", "REVOKED_WAIVER", "PHASE74_WAIVER_REGISTER_REPORT", "HIGH", "revoked waiver present"))
    if row.overdue_critical_sla:
        blockers.append("overdue_critical_sla")
        limitations.append(LimitationRecord("lim-overdue-sla", "OVERDUE_CRITICAL_SLA", "PHASE73_SLA_BUNDLE_REPORT", "CRITICAL", "critical SLA overdue"))
    if row.unsafe_waiver_attempt:
        blockers.append("unsafe_waiver_attempt")
        limitations.append(LimitationRecord("lim-unsafe-waiver", "UNSAFE_WAIVER_ATTEMPT", "PHASE74_WAIVER_REGISTER_REPORT", "CRITICAL", "unsafe waiver attempt detected"))
    if row.ambiguous_signoff_linkage:
        errors.append("ambiguous_signoff_linkage")
        limitations.append(LimitationRecord("lim-signoff-linkage", "AMBIGUOUS_SIGNOFF_LINKAGE", "PHASE70_SIGNOFF_MATRIX_REPORT", "MEDIUM", "sign-off linkage ambiguous"))
    if row.missing_rollback_evidence:
        errors.append("missing_rollback_evidence")
        limitations.append(LimitationRecord("lim-rollback", "MISSING_ROLLBACK_EVIDENCE", "ROLLBACK_READINESS_REFERENCE", "HIGH", "rollback evidence missing"))
    if row.missing_incident_response_evidence:
        errors.append("missing_incident_response_evidence")
        limitations.append(LimitationRecord("lim-incident", "MISSING_INCIDENT_RESPONSE_EVIDENCE", "INCIDENT_RESPONSE_REFERENCE", "HIGH", "incident response evidence missing"))

    marker_blockers = {
        row.invalid_xaman_payload_approval_marker: ("xaman_payload_approval_marker", "XAMAN_PAYLOAD_AMBIGUITY"),
        row.invalid_wallet_material_approval_marker: ("wallet_material_approval_marker", "WALLET_MATERIAL_AMBIGUITY"),
        row.invalid_signing_submission_autofill_approval_marker: ("signing_submission_autofill_approval_marker", "TESTNET_LIVE_APPROVAL_AMBIGUITY"),
        row.invalid_testnet_live_execution_approval_marker: ("testnet_live_execution_approval_marker", "TESTNET_LIVE_APPROVAL_AMBIGUITY"),
        row.invalid_runtime_readiness_service_marker: ("runtime_readiness_service_marker", "RUNTIME_SERVICE_AMBIGUITY"),
        row.invalid_safety_bypass_marker: ("safety_bypass_marker", "UNSAFE_WAIVER_ATTEMPT"),
    }
    for active, (blocker, category) in marker_blockers.items():
        if active:
            blockers.append(blocker)
            limitations.append(LimitationRecord(f"lim-{blocker}", category, blocker, "CRITICAL", "unsafe approval wording or marker"))

    for item in row.artifact_references:
        if item.required_classification == "REQUIRED" and not item.declared_hash:
            errors.append(f"unverifiable_artifact_hash:{item.artifact_id}")
            limitations.append(LimitationRecord(f"lim-{item.artifact_id}", "UNVERIFIABLE_ARTIFACT_HASH", item.artifact_id, "MEDIUM", "required artifact hash missing"))
        if item.artifact_status == "STALE":
            errors.append(f"stale_artifact:{item.artifact_id}")
            limitations.append(LimitationRecord(f"lim-stale-{item.artifact_id}", "STALE_ARTIFACT", item.artifact_id, "MEDIUM", "artifact marked stale"))

    if blockers:
        readiness = FINAL_BLOCKED
    elif missing_types or not all(phase_presence.values()):
        readiness = FINAL_INCOMPLETE
    elif errors:
        readiness = FINAL_REVIEW_REQUIRED if len(errors) < 4 else FINAL_NOT_READY
    else:
        readiness = FINAL_SPEC_REVIEW_READY

    spec = XamanGovernanceFinalReadinessBundleSpec(
        phase="75",
        objective="Xaman governance final readiness bundle contract spec",
        final_bundle_id=row.final_bundle_id,
        deterministic_timestamp=row.deterministic_timestamp,
        final_bundle_domains=FINAL_BUNDLE_DOMAINS,
        artifact_references=row.artifact_references,
        completeness_checks=COMPLETENESS_CHECKS,
        limitation_register=tuple(limitations),
    )
    return XamanGovernanceFinalReadinessBundleReport(row.fixture_id, spec, readiness, tuple(errors + blockers), tuple(blockers))
