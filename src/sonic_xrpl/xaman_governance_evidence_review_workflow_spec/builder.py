from __future__ import annotations

from sonic_xrpl.xaman_governance_evidence_review_workflow_spec.models import (
    WORKFLOW_BLOCKED,
    WORKFLOW_NOT_READY,
    WORKFLOW_REVIEW_REQUIRED,
    WORKFLOW_SPEC_REVIEW_READY,
    WorkflowTransition,
    XamanGovernanceEvidenceReviewWorkflowFixtureInput,
    XamanGovernanceEvidenceReviewWorkflowReport,
    XamanGovernanceEvidenceReviewWorkflowSpec,
)

ALLOWED_TRANSITIONS: tuple[WorkflowTransition, ...] = (
    WorkflowTransition("NOT_STARTED", "WAITING_FOR_EVIDENCE", True, "Evidence intake pending."),
    WorkflowTransition("WAITING_FOR_EVIDENCE", "READY_FOR_REVIEW", True, "Evidence collected."),
    WorkflowTransition("READY_FOR_REVIEW", "IN_REVIEW", True, "Reviewer accepted queue item."),
    WorkflowTransition("IN_REVIEW", "REVIEW_REQUIRED", True, "More evidence required."),
    WorkflowTransition("IN_REVIEW", "ESCALATED", True, "Escalation required."),
    WorkflowTransition("IN_REVIEW", "REJECTED", True, "Workflow item rejected."),
    WorkflowTransition("IN_REVIEW", "DEFERRED", True, "Workflow item deferred."),
    WorkflowTransition("IN_REVIEW", "SPEC_REVIEW_READY", True, "Spec-only readiness met."),
    WorkflowTransition("IN_REVIEW", "BLOCKED", True, "Unsafe marker or blocker detected."),
)


def build_xaman_governance_evidence_review_workflow_spec(
    row: XamanGovernanceEvidenceReviewWorkflowFixtureInput,
) -> XamanGovernanceEvidenceReviewWorkflowReport:
    errors: list[str] = []
    blockers: list[str] = []

    if not row.steps:
        errors.append("missing_workflow_steps")
    if not row.handoffs:
        errors.append("missing_handoffs")
    if not row.has_evidence_intake:
        errors.append("missing_evidence_intake")
    if not row.has_dependency_report:
        errors.append("missing_dependency_report")
    if not row.has_safety_scan_triage:
        errors.append("missing_safety_scan_triage")
    if not row.has_rollback_evidence:
        errors.append("missing_rollback_evidence")
    if not row.has_incident_response_evidence:
        errors.append("missing_incident_response_evidence")

    for step in row.steps:
        if step.status == "SPEC_REVIEW_READY" and (
            row.invalid_payload_testnet_live_marker
            or row.invalid_wallet_material_ambiguity_marker
            or row.invalid_runtime_workflow_marker
        ):
            errors.append(f"unsafe_ready_state:{step.step_id}")
        if step.status not in {
            "NOT_STARTED",
            "WAITING_FOR_EVIDENCE",
            "READY_FOR_REVIEW",
            "IN_REVIEW",
            "REVIEW_REQUIRED",
            "ESCALATED",
            "REJECTED",
            "DEFERRED",
            "BLOCKED",
            "SPEC_REVIEW_READY",
        }:
            errors.append(f"unknown_status:{step.step_id}")

    if row.invalid_payload_testnet_live_marker:
        blockers.append("blocked_invalid_payload_testnet_live_marker")
    if row.invalid_wallet_material_ambiguity_marker:
        blockers.append("blocked_invalid_wallet_material_ambiguity_marker")
    if row.invalid_runtime_workflow_marker:
        blockers.append("blocked_invalid_runtime_workflow_marker")
    errors.extend(blockers)

    if blockers:
        readiness = WORKFLOW_BLOCKED
    elif errors:
        if len(errors) >= 6:
            readiness = WORKFLOW_NOT_READY
        else:
            readiness = WORKFLOW_REVIEW_REQUIRED
    else:
        readiness = WORKFLOW_SPEC_REVIEW_READY

    spec = XamanGovernanceEvidenceReviewWorkflowSpec(
        phase="72",
        objective="Xaman governance evidence review workflow contract spec",
        workflow_id=row.workflow_id,
        steps=row.steps,
        transitions=ALLOWED_TRANSITIONS,
        handoffs=row.handoffs,
        escalations=row.escalations,
    )
    return XamanGovernanceEvidenceReviewWorkflowReport(
        fixture_id=row.fixture_id,
        spec=spec,
        readiness_classification=readiness,
        validation_errors=tuple(errors),
        blockers=tuple(blockers),
    )
