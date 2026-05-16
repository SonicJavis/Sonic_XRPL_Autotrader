from __future__ import annotations

from sonic_xrpl.xaman_dry_run_readiness_review_spec.models import ReadinessRequirement

READINESS_REQUIREMENTS: tuple[ReadinessRequirement, ...] = (
    ReadinessRequirement("manual_approval_design_reference", "Manual approval design reference", True, "Requires Phase 61 design contracts."),
    ReadinessRequirement("payload_schema_spec_reference", "Payload schema spec reference", True, "Requires Phase 62 payload schema contracts."),
    ReadinessRequirement("callback_verification_spec_reference", "Callback verification spec reference", True, "Requires Phase 63 callback/replay contracts."),
    ReadinessRequirement("audit_idempotency_spec_reference", "Audit/idempotency spec reference", True, "Requires Phase 64 idempotency contracts."),
    ReadinessRequirement("approval_state_machine_spec_reference", "Approval state-machine spec reference", True, "Requires Phase 65 transition contracts."),
    ReadinessRequirement("operator_consent_ux_reference", "Operator consent UX spec reference", True, "Requires Phase 66 UX contracts."),
    ReadinessRequirement("consent_evidence_pack_reference", "Consent evidence-pack reference", True, "Requires Phase 67 evidence contracts."),
    ReadinessRequirement("preflight_safety_checklist_reference", "Preflight safety checklist reference", True, "Requires Phase 68 preflight contracts."),
    ReadinessRequirement("dependency_audit_status", "Dependency audit status", True, "Requires strict dependency audit pass."),
    ReadinessRequirement("safety_grep_status", "Safety grep status", True, "Requires forbidden-pattern scan pass."),
    ReadinessRequirement("audit_validator_status", "Audit validator status", True, "Requires audit validator pass."),
    ReadinessRequirement("migration_safe_status", "Migration-safe check status", True, "Requires migration-safe controls pass."),
    ReadinessRequirement("guard_critical_status", "Guard-critical check status", True, "Requires guard-critical review pass."),
    ReadinessRequirement("no_secrets_status", "No-secrets status", True, "Confirms no secret/key material inclusion."),
    ReadinessRequirement("no_wallet_material_status", "No-wallet-material status", True, "Confirms wallet material remains blocked."),
    ReadinessRequirement("no_xaman_api_status", "No-Xaman-API status", True, "Confirms no Xaman API usage."),
    ReadinessRequirement("no_payload_created_status", "No-payload-created status", True, "Confirms no payload creation."),
    ReadinessRequirement("no_signing_submission_status", "No-signing/submission status", True, "Confirms signing/submission remain blocked."),
    ReadinessRequirement("no_testnet_execution_status", "No-testnet-execution status", True, "Confirms no testnet execution."),
    ReadinessRequirement("no_live_execution_status", "No-live-execution status", True, "Confirms no live execution."),
    ReadinessRequirement("rollback_plan_status", "Rollback plan status", True, "Requires rollback design status."),
    ReadinessRequirement("kill_switch_design_status", "Kill-switch design status", True, "Requires kill-switch design status."),
)

COMPLETENESS_REQUIREMENTS: tuple[str, ...] = (
    "All prerequisite spec references must be present.",
    "All safety gate statuses must be present.",
    "All no-execution/no-wallet/no-api/no-signing statuses must remain explicit.",
    "Dry-run readiness review pack remains spec-only and non-executing.",
)
