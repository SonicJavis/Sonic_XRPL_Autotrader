from __future__ import annotations

from sonic_xrpl.xaman_preflight_safety_checklist_spec.checklist import (
    CHECKLIST_REQUIREMENTS,
    COMPLETENESS_REQUIREMENTS,
)
from sonic_xrpl.xaman_preflight_safety_checklist_spec.models import (
    INSUFFICIENT_EVIDENCE,
    PREFLIGHT_BLOCKED,
    PREFLIGHT_SPEC_INVALID,
    PREFLIGHT_SPEC_REVIEW_REQUIRED,
    PREFLIGHT_SPEC_VALID,
    Phase68Blocker,
    XamanPreflightSafetyChecklistFixtureInput,
    XamanPreflightSafetyChecklistSpec,
    XamanPreflightSafetyChecklistSpecReport,
)


def _base_blockers() -> tuple[Phase68Blocker, ...]:
    return (
        Phase68Blocker("P6801", "CRITICAL", "No runtime checklist runner authorization", "Runtime checklist execution is out of scope in Phase 68.", True, True, True),
        Phase68Blocker("P6802", "CRITICAL", "No UI/API/runtime authorization", "UI/API/runtime implementation is blocked in Phase 68.", True, True, True),
        Phase68Blocker("P6803", "CRITICAL", "No export/persistence authorization", "Export/file-write and persistence/DB implementations are blocked.", True, True, True),
        Phase68Blocker("P6804", "CRITICAL", "No callback runtime authorization", "Callback/webhook runtime handling remains blocked.", True, True, True),
        Phase68Blocker("P6805", "CRITICAL", "No payload/API/signing/submission authorization", "Payload creation, API usage, signing, and submission remain blocked.", False, True, True),
        Phase68Blocker("P6806", "CRITICAL", "No testnet/live execution authorization", "Testnet and live execution remain blocked pending separate approval.", False, True, True),
    )


def build_xaman_preflight_safety_checklist_spec(
    row: XamanPreflightSafetyChecklistFixtureInput,
) -> XamanPreflightSafetyChecklistSpecReport:
    errors: list[str] = []
    blocked: list[str] = []

    checks = (
        ("missing_evidence_pack_gate", row.has_evidence_pack_gate),
        ("missing_payload_schema_gate", row.has_payload_schema_gate),
        ("missing_callback_verification_gate", row.has_callback_verification_gate),
        ("missing_audit_idempotency_gate", row.has_audit_idempotency_gate),
        ("missing_approval_state_machine_gate", row.has_approval_state_machine_gate),
        ("missing_operator_consent_ux_gate", row.has_operator_consent_ux_gate),
        ("missing_dependency_audit_gate", row.has_dependency_audit_gate),
        ("missing_safety_grep_gate", row.has_safety_grep_gate),
        ("missing_audit_validator_gate", row.has_audit_validator_gate),
        ("missing_migration_safe_gate", row.has_migration_safe_gate),
        ("missing_guard_critical_gate", row.has_guard_critical_gate),
        ("missing_no_secrets_gate", row.has_no_secrets_gate),
        ("missing_no_wallet_material_gate", row.has_no_wallet_material_gate),
        ("missing_no_xaman_api_gate", row.has_no_xaman_api_gate),
        ("missing_no_payload_created_gate", row.has_no_payload_created_gate),
        ("missing_no_signing_submission_gate", row.has_no_signing_submission_gate),
        ("missing_no_testnet_execution_gate", row.has_no_testnet_execution_gate),
        ("missing_no_live_execution_gate", row.has_no_live_execution_gate),
        ("missing_rollback_plan", row.has_rollback_plan),
        ("missing_kill_switch_design", row.has_kill_switch_design),
    )
    for label, present in checks:
        if not present:
            errors.append(label)

    marker_map = {
        "invalid_payload_created_marker": row.invalid_payload_created_marker,
        "invalid_xaman_called_marker": row.invalid_xaman_called_marker,
        "invalid_signing_submission_marker": row.invalid_signing_submission_marker,
        "invalid_wallet_material_marker": row.invalid_wallet_material_marker,
        "invalid_runtime_runner_marker": row.invalid_runtime_runner_marker,
        "invalid_ui_api_runtime_marker": row.invalid_ui_api_runtime_marker,
        "invalid_export_file_write_marker": row.invalid_export_file_write_marker,
        "invalid_persistence_db_write_marker": row.invalid_persistence_db_write_marker,
        "invalid_testnet_live_execution_marker": row.invalid_testnet_live_execution_marker,
    }
    for marker, enabled in marker_map.items():
        if enabled:
            errors.append(f"blocked_{marker}")
            blocked.append(marker)

    if errors:
        if any(item.startswith("blocked_") for item in errors):
            outcome = PREFLIGHT_BLOCKED
        elif len(errors) >= 12:
            outcome = INSUFFICIENT_EVIDENCE
        elif len(errors) >= 6:
            outcome = PREFLIGHT_SPEC_INVALID
        else:
            outcome = PREFLIGHT_SPEC_REVIEW_REQUIRED
    else:
        outcome = PREFLIGHT_SPEC_VALID

    spec = XamanPreflightSafetyChecklistSpec(
        phase="68",
        objective="Xaman testnet preflight safety checklist contract spec",
        checklist_id=row.checklist_id,
        candidate_id=row.candidate_id,
        checklist_requirements=CHECKLIST_REQUIREMENTS,
        completeness_requirements=COMPLETENESS_REQUIREMENTS,
        blockers=_base_blockers(),
    )

    return XamanPreflightSafetyChecklistSpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        outcome=outcome,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked),
    )
