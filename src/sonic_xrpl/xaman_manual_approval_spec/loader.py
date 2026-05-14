from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.xaman_manual_approval_spec.models import XamanSpecFixtureInput


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def load_manual_approval_spec_fixture(path: str | Path) -> XamanSpecFixtureInput:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return XamanSpecFixtureInput(
        fixture_id=str(payload.get("fixture_id") or ""),
        candidate_id=str(payload.get("candidate_id") or ""),
        issuer=str(payload.get("issuer") or ""),
        symbol=str(payload.get("symbol") or ""),
        intelligence_verdict=str(payload.get("intelligence_verdict") or ""),
        paper_simulation_reference=str(payload.get("paper_simulation_reference") or ""),
        risk_disclosure_present=_to_bool(payload.get("risk_disclosure_present", False)),
        replay_protection_present=_to_bool(payload.get("replay_protection_present", False)),
        expiry_ttl_present=_to_bool(payload.get("expiry_ttl_present", False)),
        audit_trail_present=_to_bool(payload.get("audit_trail_present", False)),
        attempted_payload_creation=_to_bool(payload.get("attempted_payload_creation", False)),
        attempted_signing=_to_bool(payload.get("attempted_signing", False)),
        attempted_submission=_to_bool(payload.get("attempted_submission", False)),
        attempted_wallet_material=_to_bool(payload.get("attempted_wallet_material", False)),
        attempted_live_execution=_to_bool(payload.get("attempted_live_execution", False)),
        future_testnet_requested=_to_bool(payload.get("future_testnet_requested", False)),
        future_mainnet_requested=_to_bool(payload.get("future_mainnet_requested", False)),
    )
