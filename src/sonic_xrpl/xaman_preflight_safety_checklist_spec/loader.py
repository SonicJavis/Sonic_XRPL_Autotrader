from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_preflight_safety_checklist_spec.models import (
    XamanPreflightSafetyChecklistFixtureInput,
)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_xaman_preflight_safety_checklist_fixture(
    path: str | Path,
) -> XamanPreflightSafetyChecklistFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanPreflightSafetyChecklistFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        checklist_id=str(payload.get("checklist_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        has_evidence_pack_gate=_to_bool(payload.get("has_evidence_pack_gate", False)),
        has_payload_schema_gate=_to_bool(payload.get("has_payload_schema_gate", False)),
        has_callback_verification_gate=_to_bool(payload.get("has_callback_verification_gate", False)),
        has_audit_idempotency_gate=_to_bool(payload.get("has_audit_idempotency_gate", False)),
        has_approval_state_machine_gate=_to_bool(payload.get("has_approval_state_machine_gate", False)),
        has_operator_consent_ux_gate=_to_bool(payload.get("has_operator_consent_ux_gate", False)),
        has_dependency_audit_gate=_to_bool(payload.get("has_dependency_audit_gate", False)),
        has_safety_grep_gate=_to_bool(payload.get("has_safety_grep_gate", False)),
        has_audit_validator_gate=_to_bool(payload.get("has_audit_validator_gate", False)),
        has_migration_safe_gate=_to_bool(payload.get("has_migration_safe_gate", False)),
        has_guard_critical_gate=_to_bool(payload.get("has_guard_critical_gate", False)),
        has_no_secrets_gate=_to_bool(payload.get("has_no_secrets_gate", False)),
        has_no_wallet_material_gate=_to_bool(payload.get("has_no_wallet_material_gate", False)),
        has_no_xaman_api_gate=_to_bool(payload.get("has_no_xaman_api_gate", False)),
        has_no_payload_created_gate=_to_bool(payload.get("has_no_payload_created_gate", False)),
        has_no_signing_submission_gate=_to_bool(payload.get("has_no_signing_submission_gate", False)),
        has_no_testnet_execution_gate=_to_bool(payload.get("has_no_testnet_execution_gate", False)),
        has_no_live_execution_gate=_to_bool(payload.get("has_no_live_execution_gate", False)),
        has_rollback_plan=_to_bool(payload.get("has_rollback_plan", False)),
        has_kill_switch_design=_to_bool(payload.get("has_kill_switch_design", False)),
        invalid_payload_created_marker=_to_bool(payload.get("invalid_payload_created_marker", False)),
        invalid_xaman_called_marker=_to_bool(payload.get("invalid_xaman_called_marker", False)),
        invalid_signing_submission_marker=_to_bool(payload.get("invalid_signing_submission_marker", False)),
        invalid_wallet_material_marker=_to_bool(payload.get("invalid_wallet_material_marker", False)),
        invalid_runtime_runner_marker=_to_bool(payload.get("invalid_runtime_runner_marker", False)),
        invalid_ui_api_runtime_marker=_to_bool(payload.get("invalid_ui_api_runtime_marker", False)),
        invalid_export_file_write_marker=_to_bool(payload.get("invalid_export_file_write_marker", False)),
        invalid_persistence_db_write_marker=_to_bool(payload.get("invalid_persistence_db_write_marker", False)),
        invalid_testnet_live_execution_marker=_to_bool(payload.get("invalid_testnet_live_execution_marker", False)),
    )
