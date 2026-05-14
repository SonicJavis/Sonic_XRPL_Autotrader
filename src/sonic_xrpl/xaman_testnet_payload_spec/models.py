from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Phase62SafetyFlags:
    design_spec_only: bool = True
    manual_approval_required: bool = True
    payload_creation_allowed: bool = False
    xaman_api_calls_allowed: bool = False
    signing_allowed: bool = False
    submission_allowed: bool = False
    autofill_allowed: bool = False
    wallet_material_allowed: bool = False
    live_execution_allowed: bool = False
    runtime_mutation_allowed: bool = False


@dataclass(frozen=True)
class PayloadSchemaRequirement:
    payload_schema_version: str
    network_required: str
    allowed_networks: tuple[str, ...]
    tx_type_allowlist_required: bool
    max_payload_ttl_seconds: int
    min_payload_ttl_seconds: int
    nonce_required: bool
    deterministic_reference_id_required: bool


@dataclass(frozen=True)
class VerificationRequirement:
    callback_signature_required: bool
    callback_timestamp_window_seconds: int
    callback_replay_cache_required: bool
    account_txn_id_required: bool
    pre_submit_verification_required: bool
    post_submit_verification_required: bool


@dataclass(frozen=True)
class TestnetGateRequirement:
    testnet_only: bool
    mainnet_blocked: bool
    explorer_verification_required: bool
    human_dual_confirmation_required: bool
    dry_run_reconciliation_required: bool


@dataclass(frozen=True)
class Phase62Blocker:
    blocker_id: str
    severity: str
    title: str
    detail: str
    required_before_testnet_impl: bool
    required_before_mainnet_impl: bool


@dataclass(frozen=True)
class XamanTestnetPayloadSpec:
    phase: str
    objective: str
    candidate_id: str
    schema: PayloadSchemaRequirement
    verification: VerificationRequirement
    testnet_gate: TestnetGateRequirement
    blockers: tuple[Phase62Blocker, ...] = field(default_factory=tuple)
    safety_flags: Phase62SafetyFlags = Phase62SafetyFlags()


@dataclass(frozen=True)
class XamanTestnetFixtureInput:
    fixture_id: str
    candidate_id: str
    requested_network: str
    payload_ttl_seconds: int | None
    nonce_present: bool
    deterministic_reference_id_present: bool
    callback_signature_present: bool
    callback_replay_cache_present: bool
    account_txn_id_present: bool
    pre_submit_verification_present: bool
    post_submit_verification_present: bool
    attempted_payload_creation: bool = False
    attempted_signing: bool = False
    attempted_submission: bool = False
    attempted_xaman_api_call: bool = False
    attempted_wallet_material: bool = False
    attempted_live_execution: bool = False


@dataclass(frozen=True)
class XamanTestnetSpecReport:
    fixture_id: str
    spec: XamanTestnetPayloadSpec
    valid_design_spec: bool
    validation_errors: tuple[str, ...]
    blocked_actions: tuple[str, ...]


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {k: jsonable(getattr(value, k)) for k in value.__dataclass_fields__}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return value
