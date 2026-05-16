from __future__ import annotations

from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec.models import (
    SLA_BLOCKED,
    SLA_NOT_READY,
    SLA_OVERDUE,
    SLA_REVIEW_REQUIRED,
    SLA_SPEC_REVIEW_READY,
    XamanGovernanceEscalationResolutionSLAFixtureInput,
    XamanGovernanceEscalationResolutionSLAReport,
    XamanGovernanceEscalationResolutionSLASpec,
)

ALLOWED_STATUSES = {
    "OPEN",
    "AWAITING_EVIDENCE",
    "IN_REVIEW",
    "RESOLVED_FOR_SPEC_REVIEW",
    "DEFERRED",
    "REJECTED",
    "OVERDUE",
    "EXPIRED",
    "BLOCKED",
    "SUPERSEDED",
}


def build_xaman_governance_escalation_resolution_sla_spec(
    row: XamanGovernanceEscalationResolutionSLAFixtureInput,
) -> XamanGovernanceEscalationResolutionSLAReport:
    errors: list[str] = []
    blockers: list[str] = []

    if not row.sla_records:
        errors.append("missing_sla_records")
    if not row.resolution_evidence_records:
        errors.append("missing_resolution_evidence_records")

    if not row.has_dependency_audit_resolution:
        errors.append("missing_dependency_audit_resolution")
    if not row.has_safety_scan_triage_resolution:
        errors.append("missing_safety_scan_triage_resolution")

    has_overdue = False
    has_review_required = False
    has_not_ready = False

    for rec in row.sla_records:
        if rec.current_status not in ALLOWED_STATUSES:
            errors.append(f"unknown_status:{rec.sla_id}")
        if not rec.owner_role.strip():
            errors.append(f"missing_owner_role:{rec.sla_id}")
        if rec.current_status in {"AWAITING_EVIDENCE", "OPEN"}:
            has_not_ready = True
        if rec.current_status in {"DEFERRED", "REJECTED", "SUPERSEDED", "IN_REVIEW"}:
            has_review_required = True
        if rec.current_status in {"OVERDUE", "EXPIRED"} or rec.overdue_classification == "OVERDUE":
            has_overdue = True
        if rec.severity in {"CRITICAL", "BLOCKING"} and rec.current_status in {"OVERDUE", "EXPIRED"}:
            blockers.append(f"critical_escalation_unresolved:{rec.sla_id}")
    for rec in row.resolution_evidence_records:
        if rec.accepted_for_spec_review and rec.evidence_integrity_status in {"STALE", "MISSING", "UNVERIFIED"}:
            errors.append(f"invalid_resolution_evidence_integrity:{rec.resolution_evidence_id}")
        if rec.accepted_for_spec_review and rec.workflow_linkage_status in {"MISSING", "AMBIGUOUS"}:
            errors.append(f"invalid_workflow_linkage:{rec.resolution_evidence_id}")
        if rec.accepted_for_spec_review and rec.attestation_linkage_status in {"MISSING", "AMBIGUOUS"}:
            errors.append(f"invalid_attestation_linkage:{rec.resolution_evidence_id}")

    if row.invalid_payload_testnet_live_marker:
        blockers.append("blocked_invalid_payload_testnet_live_marker")
    if row.invalid_wallet_material_ambiguity_marker:
        blockers.append("blocked_invalid_wallet_material_ambiguity_marker")
    if row.invalid_runtime_sla_scheduler_marker:
        blockers.append("blocked_invalid_runtime_sla_scheduler_marker")
    if row.invalid_runtime_notification_marker:
        blockers.append("blocked_invalid_runtime_notification_marker")

    if blockers:
        readiness = SLA_BLOCKED
    elif has_overdue:
        readiness = SLA_OVERDUE
    elif errors:
        readiness = SLA_NOT_READY if len(errors) >= 4 else SLA_REVIEW_REQUIRED
    elif has_not_ready:
        readiness = SLA_NOT_READY
    elif has_review_required:
        readiness = SLA_REVIEW_REQUIRED
    else:
        readiness = SLA_SPEC_REVIEW_READY

    spec = XamanGovernanceEscalationResolutionSLASpec(
        phase="73",
        objective="Xaman governance escalation resolution SLA contract spec",
        sla_bundle_id=row.sla_bundle_id,
        sla_records=row.sla_records,
        resolution_evidence_records=row.resolution_evidence_records,
    )
    return XamanGovernanceEscalationResolutionSLAReport(
        fixture_id=row.fixture_id,
        spec=spec,
        readiness_classification=readiness,
        validation_errors=tuple(errors + blockers),
        blockers=tuple(blockers),
    )
