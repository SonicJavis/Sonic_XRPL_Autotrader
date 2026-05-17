from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_governance_exception_waiver_register_spec.models import (
    WaiverRequestRecord,
    XamanGovernanceExceptionWaiverRegisterFixtureInput,
)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _tuple(payload, key: str) -> tuple[str, ...]:
    return tuple(str(item) for item in payload.get(key, []))


def _load_waiver_record(payload: dict) -> WaiverRequestRecord:
    return WaiverRequestRecord(
        waiver_id=str(payload.get("waiver_id", "")),
        waiver_domain=str(payload.get("waiver_domain", "")),
        severity=str(payload.get("severity", "")),
        requester_role=str(payload.get("requester_role", "")),
        reviewer_role=str(payload.get("reviewer_role", "")),
        related_phase70_signoff_domain=str(payload.get("related_phase70_signoff_domain", "")),
        related_phase71_attestation_id=str(payload.get("related_phase71_attestation_id", "")),
        related_phase72_workflow_step_id=str(payload.get("related_phase72_workflow_step_id", "")),
        related_phase73_sla_escalation_id=str(payload.get("related_phase73_sla_escalation_id", "")),
        requested_exception_summary=str(payload.get("requested_exception_summary", "")),
        required_evidence_ids=_tuple(payload, "required_evidence_ids"),
        supplied_evidence_ids=_tuple(payload, "supplied_evidence_ids"),
        stale_evidence_ids=_tuple(payload, "stale_evidence_ids"),
        risk_acceptance_rationale=str(payload.get("risk_acceptance_rationale", "")),
        compensating_control_references=_tuple(payload, "compensating_control_references"),
        expiry_policy=str(payload.get("expiry_policy", "")),
        revocation_policy=str(payload.get("revocation_policy", "")),
        current_status=str(payload.get("current_status", "")),
        limitation_notes=str(payload.get("limitation_notes", "")),
        docs_only_spec_only=_to_bool(payload.get("docs_only_spec_only", False)),
        replacement_waiver_id=str(payload.get("replacement_waiver_id", "")),
        safety_flags=_tuple(payload, "safety_flags"),
        dependency_risk_classification=str(payload.get("dependency_risk_classification", "")),
    )


def load_xaman_governance_exception_waiver_register_fixture(
    path: str | Path,
) -> XamanGovernanceExceptionWaiverRegisterFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanGovernanceExceptionWaiverRegisterFixtureInput(
        fixture_id=str(payload.get("fixture_id", "")),
        waiver_register_id=str(payload.get("waiver_register_id", "")),
        deterministic_timestamp=str(payload.get("deterministic_timestamp", "")),
        waiver_records=tuple(_load_waiver_record(i) for i in payload.get("waiver_records", [])),
        has_dependency_audit_resolution=_to_bool(payload.get("has_dependency_audit_resolution", False)),
        has_safety_scan_triage_resolution=_to_bool(payload.get("has_safety_scan_triage_resolution", False)),
        invalid_xaman_payload_waiver_marker=_to_bool(payload.get("invalid_xaman_payload_waiver_marker", False)),
        invalid_wallet_material_waiver_marker=_to_bool(payload.get("invalid_wallet_material_waiver_marker", False)),
        invalid_signing_submission_autofill_waiver_marker=_to_bool(payload.get("invalid_signing_submission_autofill_waiver_marker", False)),
        invalid_testnet_live_execution_waiver_marker=_to_bool(payload.get("invalid_testnet_live_execution_waiver_marker", False)),
        invalid_runtime_mutation_waiver_marker=_to_bool(payload.get("invalid_runtime_mutation_waiver_marker", False)),
        invalid_guard_weakening_waiver_marker=_to_bool(payload.get("invalid_guard_weakening_waiver_marker", False)),
        invalid_safety_bypass_marker=_to_bool(payload.get("invalid_safety_bypass_marker", False)),
    )
