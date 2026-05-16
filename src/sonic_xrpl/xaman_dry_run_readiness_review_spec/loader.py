from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_dry_run_readiness_review_spec.models import (
    XamanDryRunReadinessFixtureInput,
)


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_xaman_dry_run_readiness_fixture(
    path: str | Path,
) -> XamanDryRunReadinessFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return XamanDryRunReadinessFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        readiness_pack_id=str(payload.get("readiness_pack_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        has_manual_approval_design_reference=_to_bool(payload.get("has_manual_approval_design_reference", False)),
        has_payload_schema_spec_reference=_to_bool(payload.get("has_payload_schema_spec_reference", False)),
        has_callback_verification_spec_reference=_to_bool(payload.get("has_callback_verification_spec_reference", False)),
        has_audit_idempotency_spec_reference=_to_bool(payload.get("has_audit_idempotency_spec_reference", False)),
        has_approval_state_machine_spec_reference=_to_bool(payload.get("has_approval_state_machine_spec_reference", False)),
        has_operator_consent_ux_reference=_to_bool(payload.get("has_operator_consent_ux_reference", False)),
        has_consent_evidence_pack_reference=_to_bool(payload.get("has_consent_evidence_pack_reference", False)),
        has_preflight_safety_checklist_reference=_to_bool(payload.get("has_preflight_safety_checklist_reference", False)),
        has_dependency_audit_status=_to_bool(payload.get("has_dependency_audit_status", False)),
        has_safety_grep_status=_to_bool(payload.get("has_safety_grep_status", False)),
        has_audit_validator_status=_to_bool(payload.get("has_audit_validator_status", False)),
        has_migration_safe_status=_to_bool(payload.get("has_migration_safe_status", False)),
        has_guard_critical_status=_to_bool(payload.get("has_guard_critical_status", False)),
        has_no_secrets_status=_to_bool(payload.get("has_no_secrets_status", False)),
        has_no_wallet_material_status=_to_bool(payload.get("has_no_wallet_material_status", False)),
        has_no_xaman_api_status=_to_bool(payload.get("has_no_xaman_api_status", False)),
        has_no_payload_created_status=_to_bool(payload.get("has_no_payload_created_status", False)),
        has_no_signing_submission_status=_to_bool(payload.get("has_no_signing_submission_status", False)),
        has_no_testnet_execution_status=_to_bool(payload.get("has_no_testnet_execution_status", False)),
        has_no_live_execution_status=_to_bool(payload.get("has_no_live_execution_status", False)),
        has_rollback_plan_status=_to_bool(payload.get("has_rollback_plan_status", False)),
        has_kill_switch_design_status=_to_bool(payload.get("has_kill_switch_design_status", False)),
        invalid_payload_created_marker=_to_bool(payload.get("invalid_payload_created_marker", False)),
        invalid_xaman_called_marker=_to_bool(payload.get("invalid_xaman_called_marker", False)),
        invalid_signing_submission_marker=_to_bool(payload.get("invalid_signing_submission_marker", False)),
        invalid_wallet_material_marker=_to_bool(payload.get("invalid_wallet_material_marker", False)),
        invalid_runtime_runner_marker=_to_bool(payload.get("invalid_runtime_runner_marker", False)),
        invalid_ui_api_runtime_marker=_to_bool(payload.get("invalid_ui_api_runtime_marker", False)),
        invalid_export_file_write_marker=_to_bool(payload.get("invalid_export_file_write_marker", False)),
        invalid_persistence_db_write_marker=_to_bool(payload.get("invalid_persistence_db_write_marker", False)),
        invalid_testnet_live_execution_marker=_to_bool(payload.get("invalid_testnet_live_execution_marker", False)),
        invalid_testnet_approved_marker=_to_bool(payload.get("invalid_testnet_approved_marker", False)),
        invalid_live_approved_marker=_to_bool(payload.get("invalid_live_approved_marker", False)),
    )
