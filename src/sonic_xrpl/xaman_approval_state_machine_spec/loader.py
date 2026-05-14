from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_approval_state_machine_spec.models import XamanApprovalStateMachineFixtureInput


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_xaman_approval_state_machine_fixture(path: str | Path) -> XamanApprovalStateMachineFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return XamanApprovalStateMachineFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        has_operator_approval_transition=_to_bool(payload.get("has_operator_approval_transition", False)),
        has_callback_verification_transition=_to_bool(payload.get("has_callback_verification_transition", False)),
        has_audit_required_transition=_to_bool(payload.get("has_audit_required_transition", False)),
        has_idempotency_requirement=_to_bool(payload.get("has_idempotency_requirement", False)),
        has_ttl_replay_requirement=_to_bool(payload.get("has_ttl_replay_requirement", False)),
        has_invalid_direct_callback_to_final_block=_to_bool(payload.get("has_invalid_direct_callback_to_final_block", False)),
        has_invalid_duplicate_callback_accept_block=_to_bool(payload.get("has_invalid_duplicate_callback_accept_block", False)),
        has_invalid_replay_accept_block=_to_bool(payload.get("has_invalid_replay_accept_block", False)),
        has_invalid_expired_to_approved_block=_to_bool(payload.get("has_invalid_expired_to_approved_block", False)),
        attempted_payload_creation_transition=_to_bool(payload.get("attempted_payload_creation_transition", False)),
        attempted_xaman_api_transition=_to_bool(payload.get("attempted_xaman_api_transition", False)),
        attempted_signing_submission_transition=_to_bool(payload.get("attempted_signing_submission_transition", False)),
        attempted_wallet_material_transition=_to_bool(payload.get("attempted_wallet_material_transition", False)),
        attempted_runtime_state_machine_marker=_to_bool(payload.get("attempted_runtime_state_machine_marker", False)),
        attempted_db_write_persistence_marker=_to_bool(payload.get("attempted_db_write_persistence_marker", False)),
        attempted_testnet_live_execution_marker=_to_bool(payload.get("attempted_testnet_live_execution_marker", False)),
    )
