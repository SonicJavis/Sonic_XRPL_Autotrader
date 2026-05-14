from __future__ import annotations

from sonic_xrpl.xaman_approval_state_machine_spec.models import (
    INSUFFICIENT_EVIDENCE,
    Phase65Blocker,
    SPEC_INVALID,
    SPEC_REVIEW_REQUIRED,
    SPEC_VALID,
    TRANSITION_BLOCKED,
    XamanApprovalStateMachineFixtureInput,
    XamanApprovalStateMachineSpec,
    XamanApprovalStateMachineSpecReport,
)
from sonic_xrpl.xaman_approval_state_machine_spec.states import ALLOWED_STATES
from sonic_xrpl.xaman_approval_state_machine_spec.transitions import INVALID_TRANSITIONS, VALID_TRANSITIONS


def _base_blockers() -> tuple[Phase65Blocker, ...]:
    return (
        Phase65Blocker("P6501", "CRITICAL", "No runtime state machine authorization", "Runtime state machine implementation is out of scope for Phase 65.", True, True, True),
        Phase65Blocker("P6502", "CRITICAL", "No persistence/DB authorization", "Persistence and database writes are not authorized in this phase.", True, True, True),
        Phase65Blocker("P6503", "CRITICAL", "No callback runtime authorization", "Callback/webhook runtime handling is blocked in this phase.", True, True, True),
        Phase65Blocker("P6504", "CRITICAL", "No payload/API/signing/submission authorization", "Payload creation, API usage, signing, and submission remain blocked.", False, True, True),
        Phase65Blocker("P6505", "CRITICAL", "No testnet/live execution authorization", "Testnet and live execution remain blocked pending separate approval.", False, True, True),
    )


def build_xaman_approval_state_machine_spec(row: XamanApprovalStateMachineFixtureInput) -> XamanApprovalStateMachineSpecReport:
    errors: list[str] = []
    blocked: list[str] = []

    if not row.has_operator_approval_transition:
        errors.append("missing_operator_approval_transition")
    if not row.has_callback_verification_transition:
        errors.append("missing_callback_verification_transition")
    if not row.has_audit_required_transition:
        errors.append("missing_audit_required_transition")
    if not row.has_idempotency_requirement:
        errors.append("missing_idempotency_requirement")
    if not row.has_ttl_replay_requirement:
        errors.append("missing_ttl_replay_requirement")
    if not row.has_invalid_direct_callback_to_final_block:
        errors.append("missing_invalid_direct_callback_to_final_block")
    if not row.has_invalid_duplicate_callback_accept_block:
        errors.append("missing_invalid_duplicate_callback_accept_block")
    if not row.has_invalid_replay_accept_block:
        errors.append("missing_invalid_replay_accept_block")
    if not row.has_invalid_expired_to_approved_block:
        errors.append("missing_invalid_expired_to_approved_block")

    marker_map = {
        "attempted_payload_creation_transition": row.attempted_payload_creation_transition,
        "attempted_xaman_api_transition": row.attempted_xaman_api_transition,
        "attempted_signing_submission_transition": row.attempted_signing_submission_transition,
        "attempted_wallet_material_transition": row.attempted_wallet_material_transition,
        "attempted_runtime_state_machine_marker": row.attempted_runtime_state_machine_marker,
        "attempted_db_write_persistence_marker": row.attempted_db_write_persistence_marker,
        "attempted_testnet_live_execution_marker": row.attempted_testnet_live_execution_marker,
    }
    for marker, enabled in marker_map.items():
        if enabled:
            errors.append(f"blocked_{marker}")
            blocked.append(marker)

    if errors:
        if any(item.startswith("blocked_") for item in errors):
            outcome = TRANSITION_BLOCKED
        elif len(errors) >= 6:
            outcome = INSUFFICIENT_EVIDENCE
        elif len(errors) >= 3:
            outcome = SPEC_INVALID
        else:
            outcome = SPEC_REVIEW_REQUIRED
    else:
        outcome = SPEC_VALID

    spec = XamanApprovalStateMachineSpec(
        phase="65",
        objective="Xaman testnet approval state machine design spec",
        candidate_id=row.candidate_id,
        allowed_states=ALLOWED_STATES,
        transition_requirements=VALID_TRANSITIONS,
        invalid_transition_rules=INVALID_TRANSITIONS,
        blockers=_base_blockers(),
    )

    return XamanApprovalStateMachineSpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        outcome=outcome,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked),
    )
