from __future__ import annotations

from sonic_xrpl.xaman_testnet_payload_spec.models import (
    PayloadSchemaRequirement,
    Phase62Blocker,
    TestnetGateRequirement,
    VerificationRequirement,
    XamanTestnetFixtureInput,
    XamanTestnetPayloadSpec,
    XamanTestnetSpecReport,
)

_ALLOWED_NETWORKS = ("xrpl-testnet", "xrpl-devnet")
_MIN_TTL = 30
_MAX_TTL = 900


def _base_blockers() -> tuple[Phase62Blocker, ...]:
    return (
        Phase62Blocker("P6201", "CRITICAL", "No payload implementation authorization", "Phase 62 is schema/verification design only.", True, True),
        Phase62Blocker("P6202", "CRITICAL", "No Xaman API integration authorization", "No API calls or SDK usage approved.", True, True),
        Phase62Blocker("P6203", "HIGH", "No callback signature implementation", "Signature verification design exists; implementation absent.", True, True),
        Phase62Blocker("P6204", "HIGH", "No replay cache implementation", "Replay cache required before any callback acceptance.", True, True),
        Phase62Blocker("P6205", "HIGH", "No testnet kill-switch execution harness", "Kill-switch design required before testnet trial.", True, True),
        Phase62Blocker("P6206", "CRITICAL", "Mainnet path blocked", "Mainnet remains blocked pending separate approval phase.", False, True),
    )


def build_xaman_testnet_payload_spec(row: XamanTestnetFixtureInput) -> XamanTestnetSpecReport:
    errors: list[str] = []
    blocked: list[str] = []

    if row.requested_network not in _ALLOWED_NETWORKS:
        errors.append("invalid_or_blocked_network")

    ttl = row.payload_ttl_seconds
    if ttl is None:
        errors.append("missing_payload_ttl")
    elif ttl < _MIN_TTL or ttl > _MAX_TTL:
        errors.append("payload_ttl_out_of_bounds")

    if not row.nonce_present:
        errors.append("missing_nonce")
    if not row.deterministic_reference_id_present:
        errors.append("missing_deterministic_reference_id")
    if not row.callback_signature_present:
        errors.append("missing_callback_signature")
    if not row.callback_replay_cache_present:
        errors.append("missing_callback_replay_cache")
    if not row.account_txn_id_present:
        errors.append("missing_account_txn_id")
    if not row.pre_submit_verification_present:
        errors.append("missing_pre_submit_verification")
    if not row.post_submit_verification_present:
        errors.append("missing_post_submit_verification")

    marker_map = {
        "attempted_payload_creation": row.attempted_payload_creation,
        "attempted_signing": row.attempted_signing,
        "attempted_submission": row.attempted_submission,
        "attempted_xaman_api_call": row.attempted_xaman_api_call,
        "attempted_wallet_material": row.attempted_wallet_material,
        "attempted_live_execution": row.attempted_live_execution,
    }
    for marker, enabled in marker_map.items():
        if enabled:
            errors.append(f"blocked_{marker}")
            blocked.append(marker)

    spec = XamanTestnetPayloadSpec(
        phase="62",
        objective="Xaman testnet payload schema and verification design review",
        candidate_id=row.candidate_id,
        schema=PayloadSchemaRequirement(
            payload_schema_version="phase62.v1",
            network_required="testnet_only",
            allowed_networks=_ALLOWED_NETWORKS,
            tx_type_allowlist_required=True,
            max_payload_ttl_seconds=_MAX_TTL,
            min_payload_ttl_seconds=_MIN_TTL,
            nonce_required=True,
            deterministic_reference_id_required=True,
        ),
        verification=VerificationRequirement(
            callback_signature_required=True,
            callback_timestamp_window_seconds=120,
            callback_replay_cache_required=True,
            account_txn_id_required=True,
            pre_submit_verification_required=True,
            post_submit_verification_required=True,
        ),
        testnet_gate=TestnetGateRequirement(
            testnet_only=True,
            mainnet_blocked=True,
            explorer_verification_required=True,
            human_dual_confirmation_required=True,
            dry_run_reconciliation_required=True,
        ),
        blockers=_base_blockers(),
    )

    return XamanTestnetSpecReport(
        fixture_id=row.fixture_id,
        spec=spec,
        valid_design_spec=not errors,
        validation_errors=tuple(errors),
        blocked_actions=tuple(blocked),
    )
