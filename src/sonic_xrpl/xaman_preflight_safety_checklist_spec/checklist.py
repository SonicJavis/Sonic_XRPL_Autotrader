from __future__ import annotations

from sonic_xrpl.xaman_preflight_safety_checklist_spec.models import ChecklistRequirement

CHECKLIST_REQUIREMENTS: tuple[ChecklistRequirement, ...] = (
    ChecklistRequirement("evidence_pack_gate", "Operator consent evidence-pack gate", True, "Requires Phase 67 evidence-pack contracts."),
    ChecklistRequirement("payload_schema_gate", "Payload schema spec gate", True, "Requires Phase 62 payload schema contracts."),
    ChecklistRequirement("callback_verification_gate", "Callback verification spec gate", True, "Requires Phase 63 callback/replay contracts."),
    ChecklistRequirement("audit_idempotency_gate", "Audit/idempotency spec gate", True, "Requires Phase 64 idempotency controls."),
    ChecklistRequirement("approval_state_machine_gate", "Approval state-machine gate", True, "Requires Phase 65 transition controls."),
    ChecklistRequirement("operator_consent_ux_gate", "Operator consent UX gate", True, "Requires Phase 66 disclosure controls."),
    ChecklistRequirement("dependency_audit_gate", "Dependency audit gate", True, "Requires strict dependency audit pass."),
    ChecklistRequirement("safety_grep_gate", "Safety grep gate", True, "Requires forbidden-pattern scan pass."),
    ChecklistRequirement("audit_validator_gate", "Audit validator gate", True, "Requires audit validator pass."),
    ChecklistRequirement("migration_safe_gate", "Migration-safe check gate", True, "Requires migration-safe controls pass."),
    ChecklistRequirement("guard_critical_gate", "Guard-critical change gate", True, "Requires guard-critical review pass."),
    ChecklistRequirement("no_secrets_gate", "No-secrets gate", True, "Confirms no secret/key material inclusion."),
    ChecklistRequirement("no_wallet_material_gate", "No-wallet-material gate", True, "Confirms wallet material remains blocked."),
    ChecklistRequirement("no_xaman_api_gate", "No-Xaman-API gate", True, "Confirms no Xaman API usage."),
    ChecklistRequirement("no_payload_created_gate", "No-payload-created gate", True, "Confirms no payload creation."),
    ChecklistRequirement("no_signing_submission_gate", "No-signing/submission gate", True, "Confirms signing/submission remain blocked."),
    ChecklistRequirement("no_testnet_execution_gate", "No-testnet-execution gate", True, "Confirms no testnet execution."),
    ChecklistRequirement("no_live_execution_gate", "No-live-execution gate", True, "Confirms no live execution."),
    ChecklistRequirement("rollback_plan", "Rollback plan requirement", True, "Requires rollback design before any future runtime phase."),
    ChecklistRequirement("kill_switch_design", "Kill-switch design requirement", True, "Requires fail-closed emergency stop design."),
)

COMPLETENESS_REQUIREMENTS: tuple[str, ...] = (
    "All prerequisite spec gates must be present.",
    "All no-execution/no-wallet/no-api/no-signing gates must remain explicit.",
    "Checklist remains spec-only and non-executing.",
    "No payload/API/signing/submission authorization.",
)
