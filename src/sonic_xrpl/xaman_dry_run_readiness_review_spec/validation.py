from __future__ import annotations

from sonic_xrpl.xaman_dry_run_readiness_review_spec.models import (
    INSUFFICIENT_EVIDENCE,
    READINESS_BLOCKED,
    READINESS_SPEC_INVALID,
    READINESS_SPEC_REVIEW_REQUIRED,
    READINESS_SPEC_VALID,
    Phase69Blocker,
    XamanDryRunReadinessFixtureInput,
    XamanDryRunReadinessReviewSpec,
    XamanDryRunReadinessSpecReport,
)
from sonic_xrpl.xaman_dry_run_readiness_review_spec.readiness import (
    COMPLETENESS_REQUIREMENTS,
    READINESS_REQUIREMENTS,
)


def _base_blockers() -> tuple[Phase69Blocker, ...]:
    return (
        Phase69Blocker("P6901", "CRITICAL", "No runtime dry-run authorization", "Runtime dry-run execution is out of scope in Phase 69.", True, True, True),
        Phase69Blocker("P6902", "CRITICAL", "No runtime checklist authorization", "Runtime checklist execution remains blocked.", True, True, True),
        Phase69Blocker("P6903", "CRITICAL", "No UI/API/runtime authorization", "UI/API/runtime implementation is blocked in Phase 69.", True, True, True),
        Phase69Blocker("P6904", "CRITICAL", "No export/persistence authorization", "Export/file-write and persistence/DB implementations are blocked.", True, True, True),
        Phase69Blocker("P6905", "CRITICAL", "No callback runtime authorization", "Callback/webhook runtime handling remains blocked.", True, True, True),
        Phase69Blocker("P6906", "CRITICAL", "No payload/API/signing/submission authorization", "Payload creation, API usage, signing, and submission remain blocked.", False, True, True),
        Phase69Blocker("P6907", "CRITICAL", "No testnet/live execution authorization", "Testnet and live execution remain blocked pending separate approval.", False, True, True),
    )


def build_xaman_dry_run_readiness_spec(
    row: XamanDryRunReadinessFixtureInput,
) -> XamanDryRunReadinessSpecReport:
    errors: list[str] = []
    blocked: list[str] = []

    checks = (
        ("missing_manual_approval_design_reference", row.has_manual_approval_design_reference),
        ("missing_payload_schema_spec_reference", row.has_payload_schema_spec_reference),
        ("missing_callback_verification_spec_reference", row.has_callback_verification_spec_reference),
        ("missing_audit_idempotency_spec_reference", row.has_audit_idempotency_spec_reference),
        ("missing_approval_state_machine_spec_reference", row.has_approval_state_machine_spec_reference),
        ("missing_operator_consent_ux_reference", row.has_operator_consent_ux_reference),
        ("missing_consent_evidence_pack_reference", row.has_consent_evidence_pack_reference),
        ("missing_preflight_safety_checklist_reference", row.has_preflight_safety_checklist_reference),
        ("missing_dependency_audit_status", row.has_dependency_audit_status),
        ("missing_safety_grep_status", row.has_safety_grep_status),
        ("missing_audit_validator_status", row.has_audit_validator_status),
        ("missing_migration_safe_status", row.has_migration_safe_status),
        ("missing_guard_critical_status", row.has_guard_critical_status),
        ("missing_no_secrets_status", row.has_no_secrets_status),
        ("missing_no_wallet_material_status", row.has_no_wallet_material_status),
        ("missing_no_xaman_api_status", row.has_no_xaman_api_status),
        ("missing_no_payload_created_status", row.has_no_payload_created_status),
        ("missing_no_signing_submission_status", row.has_no_signing_submission_status),
        ("missing_no_testnet_execution_status", row.has_no_testnet_execution_status),
        ("missing_no_live_execution_status", row.has_no_live_execution_status),
        ("missing_rollback_plan_status", row.has_rollback_plan_status),
        ("missing_kill_switch_design_status", row.has_kill_switch_design_status),
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
        "invalid_testnet_approved_marker": row.invalid_testnet_approved_marker,
        "invalid_live_approved_marker": row.invalid_live_approved_marker,
    }
    for marker, enabled in marker_map.items():
        if enabled:
            errors.append(f"blocked_{marker}")
            blocked.append(marker)

    if errors:
        if any(item.startswith("blocked_") for item in errors):
            outcome = READINESS_BLOCKED
        elif len(errors) >= 14:
            outcome = INSUFFICIENT_EVIDENCE
        elif len(errors) >= 7:
            outcome = READINESS_SPEC_INVALID
        else:
            outcome = READINESS_SPEC_REVIEW_REQUIRED
    else:
        outcome = READINESS_SPEC_VALID

    spec = XamanDryRunReadinessReviewSpec(
        phase="69",
        objective="Xaman testnet dry-run readiness review pack contract spec",
        readiness_pack_id=row.readiness_pack_id,
        candidate_id=row.candidate_id,
        readiness_requirements=READINESS_REQUIREMENTS,
        completeness_requirements=COMPLETENESS_REQUIREMENTS,
        blockers=_base_blockers(),
    )

    return XamanDryRunReadinessSpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        outcome=outcome,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked),
    )
