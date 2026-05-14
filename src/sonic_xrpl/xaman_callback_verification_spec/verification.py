from __future__ import annotations

from sonic_xrpl.xaman_callback_verification_spec.models import (
    AuditAndGateRequirements,
    CallbackFieldRequirements,
    Phase63Blocker,
    ReplayAndIdempotencyRequirements,
    XamanCallbackFixtureInput,
    XamanCallbackVerificationSpec,
    XamanCallbackVerificationSpecReport,
)

_MIN_TTL = 30
_MAX_TTL = 900
_MIN_REPLAY_WINDOW = 10
_MAX_REPLAY_WINDOW = 600


_DEF_REQUIRED_FIELDS = (
    "meta.application_uuidv4",
    "meta.payload_uuidv4",
    "meta.signed",
    "custom_meta.identifier",
)

_DEF_PROHIBITED_FIELDS = (
    "txblob",
    "wallet_seed",
    "sensitive_material",
    "private_key",
)


def _base_blockers() -> tuple[Phase63Blocker, ...]:
    return (
        Phase63Blocker("P6301", "CRITICAL", "No callback endpoint authorization", "Phase 63 is callback verification design only; no runtime handler approved.", True, True, True),
        Phase63Blocker("P6302", "CRITICAL", "No Xaman SDK/API integration authorization", "No SDK dependency or API calls are approved in this phase.", True, True, True),
        Phase63Blocker("P6303", "HIGH", "No authenticity verification implementation", "Signature/header verification remains a future implementation requirement.", True, True, True),
        Phase63Blocker("P6304", "HIGH", "No nonce/TTL persistence implementation", "Replay controls require persistent nonce/TTL state before any callback acceptance.", True, True, True),
        Phase63Blocker("P6305", "HIGH", "No idempotency store implementation", "Duplicate callback suppression requires a dedicated idempotency store.", True, True, True),
        Phase63Blocker("P6306", "HIGH", "No audit persistence implementation", "Immutable callback audit trail persistence is not implemented.", True, True, True),
        Phase63Blocker("P6307", "CRITICAL", "No payload transaction authorization", "Payload creation and transaction finalization remain blocked.", False, True, True),
        Phase63Blocker("P6308", "CRITICAL", "No testnet/live execution authorization", "Testnet and mainnet execution remain blocked pending separate explicit phases.", False, True, True),
    )


def build_xaman_callback_verification_spec(row: XamanCallbackFixtureInput) -> XamanCallbackVerificationSpecReport:
    errors: list[str] = []
    blocked: list[str] = []

    if not row.authenticity_requirement_present:
        errors.append("missing_authenticity_requirement")
    if not row.required_fields_present:
        errors.append("missing_required_callback_fields")
    if not row.prohibited_fields_declared:
        errors.append("missing_prohibited_callback_fields")
    if not row.correlation_id_present:
        errors.append("missing_correlation_id")
    if not row.payload_uuid_binding_present:
        errors.append("missing_payload_uuid_binding")
    if not row.candidate_binding_present:
        errors.append("missing_candidate_binding")
    if not row.paper_simulation_binding_present:
        errors.append("missing_paper_simulation_binding")
    if not row.nonce_requirement_present:
        errors.append("missing_nonce_requirement")
    if not row.ttl_requirement_present:
        errors.append("missing_ttl_requirement")
    if not row.idempotency_requirement_present:
        errors.append("missing_idempotency_requirement")
    if not row.duplicate_callback_handling_present:
        errors.append("missing_duplicate_callback_handling")
    if not row.callback_ordering_requirement_present:
        errors.append("missing_callback_ordering_requirement")
    if not row.audit_trail_requirement_present:
        errors.append("missing_audit_trail_requirement")
    if not row.cancellation_and_rejection_requirement_present:
        errors.append("missing_cancellation_and_rejection_requirement")
    if not row.operator_consent_linkage_present:
        errors.append("missing_operator_consent_linkage")
    if not row.testnet_gate_complete:
        errors.append("incomplete_testnet_gate")
    if not row.live_gate_blocked:
        errors.append("live_gate_not_blocked")

    if row.ttl_seconds is None:
        errors.append("missing_ttl_seconds")
    elif row.ttl_seconds < _MIN_TTL or row.ttl_seconds > _MAX_TTL:
        errors.append("ttl_seconds_out_of_bounds")

    if row.replay_window_seconds is None:
        errors.append("missing_replay_window_seconds")
    elif row.replay_window_seconds < _MIN_REPLAY_WINDOW or row.replay_window_seconds > _MAX_REPLAY_WINDOW:
        errors.append("replay_window_out_of_bounds")

    marker_map = {
        "attempted_callback_handler": row.attempted_callback_handler,
        "attempted_webhook_runtime": row.attempted_webhook_runtime,
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

    spec = XamanCallbackVerificationSpec(
        phase="63",
        objective="Xaman callback authenticity and replay verification design spec",
        candidate_id=row.candidate_id,
        callback_fields=CallbackFieldRequirements(
            required_fields=_DEF_REQUIRED_FIELDS,
            prohibited_fields=_DEF_PROHIBITED_FIELDS,
            correlation_id_required=True,
            payload_uuid_binding_required=True,
            candidate_binding_required=True,
            paper_simulation_binding_required=True,
            operator_consent_linkage_required=True,
        ),
        replay_and_idempotency=ReplayAndIdempotencyRequirements(
            nonce_required=True,
            ttl_required=True,
            ttl_min_seconds=_MIN_TTL,
            ttl_max_seconds=_MAX_TTL,
            replay_window_seconds=row.replay_window_seconds or _MIN_REPLAY_WINDOW,
            idempotency_key_required=True,
            duplicate_callback_handling_required=True,
            callback_ordering_required=True,
        ),
        audit_and_gates=AuditAndGateRequirements(
            authenticity_checklist_required=True,
            audit_trail_required=True,
            cancellation_and_rejection_handling_required=True,
            testnet_gate_checklist_required=True,
            live_readiness_blockers_required=True,
        ),
        blockers=_base_blockers(),
    )

    return XamanCallbackVerificationSpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        valid_design_spec=not errors,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked),
    )
