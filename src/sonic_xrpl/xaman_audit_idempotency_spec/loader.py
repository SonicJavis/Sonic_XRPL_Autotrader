from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_audit_idempotency_spec.models import XamanAuditIdempotencyFixtureInput


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


def load_xaman_audit_idempotency_fixture(path: str | Path) -> XamanAuditIdempotencyFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return XamanAuditIdempotencyFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        correlation_id_present=_to_bool(payload.get("correlation_id_present", False)),
        callback_event_id_present=_to_bool(payload.get("callback_event_id_present", False)),
        payload_uuid_binding_present=_to_bool(payload.get("payload_uuid_binding_present", False)),
        candidate_binding_present=_to_bool(payload.get("candidate_binding_present", False)),
        paper_simulation_binding_present=_to_bool(payload.get("paper_simulation_binding_present", False)),
        operator_approval_binding_present=_to_bool(payload.get("operator_approval_binding_present", False)),
        risk_disclosure_linkage_present=_to_bool(payload.get("risk_disclosure_linkage_present", False)),
        idempotency_key_rule_present=_to_bool(payload.get("idempotency_key_rule_present", False)),
        idempotency_conflict_policy_present=_to_bool(payload.get("idempotency_conflict_policy_present", False)),
        duplicate_callback_policy_present=_to_bool(payload.get("duplicate_callback_policy_present", False)),
        replay_policy_present=_to_bool(payload.get("replay_policy_present", False)),
        stale_callback_policy_present=_to_bool(payload.get("stale_callback_policy_present", False)),
        ttl_seconds=_to_int(payload.get("ttl_seconds")),
        append_only_required_present=_to_bool(payload.get("append_only_required_present", False)),
        tamper_evidence_required_present=_to_bool(payload.get("tamper_evidence_required_present", False)),
        retention_policy_present=_to_bool(payload.get("retention_policy_present", False)),
        redaction_policy_present=_to_bool(payload.get("redaction_policy_present", False)),
        sensitive_material_exclusion_present=_to_bool(payload.get("sensitive_material_exclusion_present", False)),
        cancellation_rejection_policy_present=_to_bool(payload.get("cancellation_rejection_policy_present", False)),
        testnet_gate_complete=_to_bool(payload.get("testnet_gate_complete", False)),
        live_gate_blocked=_to_bool(payload.get("live_gate_blocked", False)),
        attempted_database_write=_to_bool(payload.get("attempted_database_write", False)),
        attempted_persistence_implementation=_to_bool(payload.get("attempted_persistence_implementation", False)),
        attempted_callback_handler=_to_bool(payload.get("attempted_callback_handler", False)),
        attempted_xaman_api_call=_to_bool(payload.get("attempted_xaman_api_call", False)),
        attempted_payload_creation=_to_bool(payload.get("attempted_payload_creation", False)),
        attempted_signing=_to_bool(payload.get("attempted_signing", False)),
        attempted_submission=_to_bool(payload.get("attempted_submission", False)),
        attempted_wallet_material=_to_bool(payload.get("attempted_wallet_material", False)),
        attempted_testnet_execution=_to_bool(payload.get("attempted_testnet_execution", False)),
        attempted_live_execution=_to_bool(payload.get("attempted_live_execution", False)),
    )
