from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec.models import (
    EscalationSLARecord,
    ResolutionEvidenceRecord,
    XamanGovernanceEscalationResolutionSLAFixtureInput,
)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _load_sla_record(payload: dict) -> EscalationSLARecord:
    return EscalationSLARecord(
        sla_id=str(payload.get("sla_id", "")),
        escalation_id=str(payload.get("escalation_id", "")),
        workflow_step_id=str(payload.get("workflow_step_id", "")),
        attestation_id=str(payload.get("attestation_id", "")),
        signoff_domain=str(payload.get("signoff_domain", "")),
        governance_domain=str(payload.get("governance_domain", "")),
        severity=str(payload.get("severity", "")),
        owner_role=str(payload.get("owner_role", "")),
        opened_at=str(payload.get("opened_at", "")),
        due_at=str(payload.get("due_at", "")),
        due_policy=str(payload.get("due_policy", "")),
        required_resolution_evidence=str(payload.get("required_resolution_evidence", "")),
        current_status=str(payload.get("current_status", "")),
        overdue_classification=str(payload.get("overdue_classification", "")),
        expiry_classification=str(payload.get("expiry_classification", "")),
        blocker_severity_if_unresolved=str(payload.get("blocker_severity_if_unresolved", "")),
        limitation_notes=str(payload.get("limitation_notes", "")),
    )


def _load_resolution_record(payload: dict) -> ResolutionEvidenceRecord:
    return ResolutionEvidenceRecord(
        resolution_evidence_id=str(payload.get("resolution_evidence_id", "")),
        escalation_id=str(payload.get("escalation_id", "")),
        evidence_artifact_id=str(payload.get("evidence_artifact_id", "")),
        reviewer_role=str(payload.get("reviewer_role", "")),
        resolution_reason=str(payload.get("resolution_reason", "")),
        evidence_integrity_status=str(payload.get("evidence_integrity_status", "")),
        attestation_linkage_status=str(payload.get("attestation_linkage_status", "")),
        workflow_linkage_status=str(payload.get("workflow_linkage_status", "")),
        accepted_for_spec_review=_to_bool(payload.get("accepted_for_spec_review", False)),
        limitation_notes=str(payload.get("limitation_notes", "")),
    )


def load_xaman_governance_escalation_resolution_sla_fixture(
    path: str | Path,
) -> XamanGovernanceEscalationResolutionSLAFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanGovernanceEscalationResolutionSLAFixtureInput(
        fixture_id=str(payload.get("fixture_id", "")),
        sla_bundle_id=str(payload.get("sla_bundle_id", "")),
        sla_records=tuple(_load_sla_record(i) for i in payload.get("sla_records", [])),
        resolution_evidence_records=tuple(
            _load_resolution_record(i) for i in payload.get("resolution_evidence_records", [])
        ),
        has_dependency_audit_resolution=_to_bool(payload.get("has_dependency_audit_resolution", False)),
        has_safety_scan_triage_resolution=_to_bool(payload.get("has_safety_scan_triage_resolution", False)),
        invalid_payload_testnet_live_marker=_to_bool(payload.get("invalid_payload_testnet_live_marker", False)),
        invalid_wallet_material_ambiguity_marker=_to_bool(
            payload.get("invalid_wallet_material_ambiguity_marker", False)
        ),
        invalid_runtime_sla_scheduler_marker=_to_bool(payload.get("invalid_runtime_sla_scheduler_marker", False)),
        invalid_runtime_notification_marker=_to_bool(payload.get("invalid_runtime_notification_marker", False)),
    )
