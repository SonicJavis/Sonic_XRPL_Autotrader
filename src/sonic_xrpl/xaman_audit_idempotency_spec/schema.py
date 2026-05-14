from __future__ import annotations

from sonic_xrpl.xaman_audit_idempotency_spec.models import (
    AuditEnvelopeSpec,
    AuditTrailSpec,
    IdempotencySpec,
    INSUFFICIENT_EVIDENCE,
    Phase64Blocker,
    SPEC_ACCEPTED,
    SPEC_REJECTED,
    SPEC_REVIEW_REQUIRED,
    XamanAuditIdempotencyFixtureInput,
    XamanAuditIdempotencySpec,
    XamanAuditIdempotencySpecReport,
)

_MIN_TTL = 30
_MAX_TTL = 900


def _base_blockers() -> tuple[Phase64Blocker, ...]:
    return (
        Phase64Blocker("P6401", "CRITICAL", "No persistence implementation authorization", "Persistence and storage implementation are out of scope for Phase 64.", True, True, True),
        Phase64Blocker("P6402", "CRITICAL", "No callback runtime authorization", "Callback handler and webhook runtime are blocked in this phase.", True, True, True),
        Phase64Blocker("P6403", "HIGH", "No idempotency state implementation", "Idempotency state storage and conflict resolution runtime are future work.", True, True, True),
        Phase64Blocker("P6404", "HIGH", "No audit trail persistence implementation", "Append-only and tamper-evident persistence are design-only now.", True, True, True),
        Phase64Blocker("P6405", "CRITICAL", "No payload/API integration authorization", "Payload creation and Xaman API integration remain blocked.", False, True, True),
        Phase64Blocker("P6406", "CRITICAL", "No testnet/live execution authorization", "Testnet and live execution remain blocked pending explicit approval.", False, True, True),
    )


def build_xaman_audit_idempotency_spec(row: XamanAuditIdempotencyFixtureInput) -> XamanAuditIdempotencySpecReport:
    errors: list[str] = []
    blocked: list[str] = []

    if not row.correlation_id_present:
        errors.append("missing_correlation_id")
    if not row.callback_event_id_present:
        errors.append("missing_callback_event_id")
    if not row.payload_uuid_binding_present:
        errors.append("missing_payload_uuid_binding")
    if not row.candidate_binding_present:
        errors.append("missing_candidate_binding")
    if not row.paper_simulation_binding_present:
        errors.append("missing_paper_simulation_binding")
    if not row.operator_approval_binding_present:
        errors.append("missing_operator_approval_binding")
    if not row.risk_disclosure_linkage_present:
        errors.append("missing_risk_disclosure_linkage")

    if not row.idempotency_key_rule_present:
        errors.append("missing_idempotency_key_rule")
    if not row.idempotency_conflict_policy_present:
        errors.append("missing_idempotency_conflict_policy")
    if not row.duplicate_callback_policy_present:
        errors.append("missing_duplicate_callback_policy")
    if not row.replay_policy_present:
        errors.append("missing_replay_policy")
    if not row.stale_callback_policy_present:
        errors.append("missing_stale_callback_policy")

    if row.ttl_seconds is None:
        errors.append("missing_ttl_seconds")
    elif row.ttl_seconds < _MIN_TTL or row.ttl_seconds > _MAX_TTL:
        errors.append("ttl_seconds_out_of_bounds")

    if not row.append_only_required_present:
        errors.append("missing_append_only_requirement")
    if not row.tamper_evidence_required_present:
        errors.append("missing_tamper_evidence_requirement")
    if not row.retention_policy_present:
        errors.append("missing_retention_policy")
    if not row.redaction_policy_present:
        errors.append("missing_redaction_policy")
    if not row.sensitive_material_exclusion_present:
        errors.append("missing_sensitive_material_exclusion")
    if not row.cancellation_rejection_policy_present:
        errors.append("missing_cancellation_rejection_policy")

    if not row.testnet_gate_complete:
        errors.append("incomplete_testnet_gate")
    if not row.live_gate_blocked:
        errors.append("live_gate_not_blocked")

    marker_map = {
        "attempted_database_write": row.attempted_database_write,
        "attempted_persistence_implementation": row.attempted_persistence_implementation,
        "attempted_callback_handler": row.attempted_callback_handler,
        "attempted_xaman_api_call": row.attempted_xaman_api_call,
        "attempted_payload_creation": row.attempted_payload_creation,
        "attempted_signing": row.attempted_signing,
        "attempted_submission": row.attempted_submission,
        "attempted_wallet_material": row.attempted_wallet_material,
        "attempted_testnet_execution": row.attempted_testnet_execution,
        "attempted_live_execution": row.attempted_live_execution,
    }
    for marker, enabled in marker_map.items():
        if enabled:
            errors.append(f"blocked_{marker}")
            blocked.append(marker)

    if errors:
        if any(item.startswith("blocked_") for item in errors):
            outcome = SPEC_REJECTED
        elif len(errors) >= 6:
            outcome = INSUFFICIENT_EVIDENCE
        else:
            outcome = SPEC_REVIEW_REQUIRED
    else:
        outcome = SPEC_ACCEPTED

    spec = XamanAuditIdempotencySpec(
        phase="64",
        objective="Xaman testnet audit trail and idempotency store design spec",
        candidate_id=row.candidate_id,
        audit_envelope=AuditEnvelopeSpec(
            event_type_enum_required=True,
            correlation_id_required=True,
            callback_event_id_required=True,
            payload_uuid_binding_required=True,
            candidate_binding_required=True,
            paper_simulation_binding_required=True,
            operator_approval_binding_required=True,
            risk_disclosure_linkage_required=True,
        ),
        idempotency=IdempotencySpec(
            idempotency_key_required=True,
            key_derivation_rule_required=True,
            conflict_policy_required=True,
            duplicate_callback_policy_required=True,
            replay_attempt_policy_required=True,
            stale_callback_policy_required=True,
            ttl_seconds_required=True,
            ttl_min_seconds=_MIN_TTL,
            ttl_max_seconds=_MAX_TTL,
        ),
        audit_trail=AuditTrailSpec(
            append_only_required=True,
            tamper_evidence_required=True,
            retention_policy_required=True,
            redaction_policy_required=True,
            sensitive_material_exclusion_required=True,
            cancellation_rejection_policy_required=True,
        ),
        blockers=_base_blockers(),
    )

    return XamanAuditIdempotencySpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        outcome=outcome,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked),
    )
