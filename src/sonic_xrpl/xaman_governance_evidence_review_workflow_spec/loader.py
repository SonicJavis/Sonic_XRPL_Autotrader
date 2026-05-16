from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_evidence_review_workflow_spec.models import (
    EscalationRecord,
    EvidenceHandoff,
    WorkflowStep,
    XamanGovernanceEvidenceReviewWorkflowFixtureInput,
)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _load_step(payload: dict) -> WorkflowStep:
    return WorkflowStep(
        step_id=str(payload.get("step_id", "")),
        stage_type=str(payload.get("stage_type", "")),
        role=str(payload.get("role", "")),
        status=str(payload.get("status", "")),
        linked_evidence_id=str(payload.get("linked_evidence_id", "")),
        linked_attestation_id=str(payload.get("linked_attestation_id", "")),
        notes=str(payload.get("notes", "")),
    )


def _load_handoff(payload: dict) -> EvidenceHandoff:
    return EvidenceHandoff(
        handoff_id=str(payload.get("handoff_id", "")),
        from_role=str(payload.get("from_role", "")),
        to_role=str(payload.get("to_role", "")),
        evidence_id=str(payload.get("evidence_id", "")),
        attestation_id=str(payload.get("attestation_id", "")),
        governance_domain=str(payload.get("governance_domain", "")),
        handoff_reason=str(payload.get("handoff_reason", "")),
        required_action=str(payload.get("required_action", "")),
        blocker_severity_if_unresolved=str(payload.get("blocker_severity_if_unresolved", "")),
        limitation_notes=str(payload.get("limitation_notes", "")),
    )


def _load_escalation(payload: dict) -> EscalationRecord:
    return EscalationRecord(
        escalation_id=str(payload.get("escalation_id", "")),
        source_step_id=str(payload.get("source_step_id", "")),
        escalation_reason=str(payload.get("escalation_reason", "")),
        severity=str(payload.get("severity", "")),
        escalation_owner=str(payload.get("escalation_owner", "")),
        required_resolution_evidence=str(payload.get("required_resolution_evidence", "")),
        resolution_status=str(payload.get("resolution_status", "")),
        limitation_notes=str(payload.get("limitation_notes", "")),
    )


def load_xaman_governance_evidence_review_workflow_fixture(
    path: str | Path,
) -> XamanGovernanceEvidenceReviewWorkflowFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanGovernanceEvidenceReviewWorkflowFixtureInput(
        fixture_id=str(payload.get("fixture_id", "")),
        workflow_id=str(payload.get("workflow_id", "")),
        steps=tuple(_load_step(i) for i in payload.get("steps", [])),
        handoffs=tuple(_load_handoff(i) for i in payload.get("handoffs", [])),
        escalations=tuple(_load_escalation(i) for i in payload.get("escalations", [])),
        has_evidence_intake=_to_bool(payload.get("has_evidence_intake", False)),
        has_dependency_report=_to_bool(payload.get("has_dependency_report", False)),
        has_safety_scan_triage=_to_bool(payload.get("has_safety_scan_triage", False)),
        has_rollback_evidence=_to_bool(payload.get("has_rollback_evidence", False)),
        has_incident_response_evidence=_to_bool(payload.get("has_incident_response_evidence", False)),
        invalid_payload_testnet_live_marker=_to_bool(payload.get("invalid_payload_testnet_live_marker", False)),
        invalid_wallet_material_ambiguity_marker=_to_bool(payload.get("invalid_wallet_material_ambiguity_marker", False)),
        invalid_runtime_workflow_marker=_to_bool(payload.get("invalid_runtime_workflow_marker", False)),
    )
