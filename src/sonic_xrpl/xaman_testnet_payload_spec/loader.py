from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_testnet_payload_spec.models import XamanTestnetFixtureInput


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


def load_xaman_testnet_payload_fixture(path: str | Path) -> XamanTestnetFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return XamanTestnetFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        requested_network=str(payload.get("requested_network") or "").strip(),
        payload_ttl_seconds=_to_int(payload.get("payload_ttl_seconds")),
        nonce_present=_to_bool(payload.get("nonce_present", False)),
        deterministic_reference_id_present=_to_bool(payload.get("deterministic_reference_id_present", False)),
        callback_signature_present=_to_bool(payload.get("callback_signature_present", False)),
        callback_replay_cache_present=_to_bool(payload.get("callback_replay_cache_present", False)),
        account_txn_id_present=_to_bool(payload.get("account_txn_id_present", False)),
        pre_submit_verification_present=_to_bool(payload.get("pre_submit_verification_present", False)),
        post_submit_verification_present=_to_bool(payload.get("post_submit_verification_present", False)),
        attempted_payload_creation=_to_bool(payload.get("attempted_payload_creation", False)),
        attempted_signing=_to_bool(payload.get("attempted_signing", False)),
        attempted_submission=_to_bool(payload.get("attempted_submission", False)),
        attempted_xaman_api_call=_to_bool(payload.get("attempted_xaman_api_call", False)),
        attempted_wallet_material=_to_bool(payload.get("attempted_wallet_material", False)),
        attempted_live_execution=_to_bool(payload.get("attempted_live_execution", False)),
    )
