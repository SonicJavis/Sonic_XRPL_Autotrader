from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_callback_verification_spec.models import XamanCallbackFixtureInput


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_xaman_callback_verification_fixture(path: str | Path) -> XamanCallbackFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return XamanCallbackFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        authenticity_requirement_present=_to_bool(payload.get("authenticity_requirement_present", False)),
        required_fields_present=_to_bool(payload.get("required_fields_present", False)),
        prohibited_fields_declared=_to_bool(payload.get("prohibited_fields_declared", False)),
        correlation_id_present=_to_bool(payload.get("correlation_id_present", False)),
        payload_uuid_binding_present=_to_bool(payload.get("payload_uuid_binding_present", False)),
        candidate_binding_present=_to_bool(payload.get("candidate_binding_present", False)),
        paper_simulation_binding_present=_to_bool(payload.get("paper_simulation_binding_present", False)),
        nonce_requirement_present=_to_bool(payload.get("nonce_requirement_present", False)),
        ttl_requirement_present=_to_bool(payload.get("ttl_requirement_present", False)),
        ttl_seconds=_to_int(payload.get("ttl_seconds")),
        replay_window_seconds=_to_int(payload.get("replay_window_seconds")),
        idempotency_requirement_present=_to_bool(payload.get("idempotency_requirement_present", False)),
        duplicate_callback_handling_present=_to_bool(payload.get("duplicate_callback_handling_present", False)),
        callback_ordering_requirement_present=_to_bool(payload.get("callback_ordering_requirement_present", False)),
        audit_trail_requirement_present=_to_bool(payload.get("audit_trail_requirement_present", False)),
        cancellation_and_rejection_requirement_present=_to_bool(payload.get("cancellation_and_rejection_requirement_present", False)),
        operator_consent_linkage_present=_to_bool(payload.get("operator_consent_linkage_present", False)),
        testnet_gate_complete=_to_bool(payload.get("testnet_gate_complete", False)),
        live_gate_blocked=_to_bool(payload.get("live_gate_blocked", False)),
        attempted_callback_handler=_to_bool(payload.get("attempted_callback_handler", False)),
        attempted_webhook_runtime=_to_bool(payload.get("attempted_webhook_runtime", False)),
        attempted_xaman_api_call=_to_bool(payload.get("attempted_xaman_api_call", False)),
        attempted_payload_creation=_to_bool(payload.get("attempted_payload_creation", False)),
        attempted_signing=_to_bool(payload.get("attempted_signing", False)),
        attempted_submission=_to_bool(payload.get("attempted_submission", False)),
        attempted_wallet_material=_to_bool(payload.get("attempted_wallet_material", False)),
        attempted_testnet_execution=_to_bool(payload.get("attempted_testnet_execution", False)),
        attempted_live_execution=_to_bool(payload.get("attempted_live_execution", False)),
    )
