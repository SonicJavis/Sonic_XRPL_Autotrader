"""AMM snapshot builder — Phase 47.

Reads AMM data from fixture store. No live calls. No swap simulation.
Capability check: AMM amendment must be ENABLED before building a real AMM snapshot.
"""

from __future__ import annotations

import hashlib
from typing import Any

from sonic_xrpl.market.models import AMMSnapshot
from sonic_xrpl.protocol.capability_matrix import is_capability_available

_AMM_CAPABILITY = "AMM"
_AMM_CLAWBACK_CAPABILITY = "AMMClawback"
_CLAWBACK_CAPABILITY = "Clawback"


def _amm_id(asset_a: str, asset_b: str, amm_account: str) -> str:
    """Deterministic AMM snapshot ID."""
    raw = f"{asset_a}|{asset_b}|{amm_account}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _normalise_asset_key(raw: Any) -> str:
    """Normalise an AMM asset to a canonical key string.

    XRP → "XRP"
    IOU → "USD:rIssuer..."  (currency:issuer — NEVER collapse same-ticker different-issuer)
    """
    if isinstance(raw, str):
        # Might be drops string (XRP) or already normalised
        try:
            int(raw)
            return "XRP"
        except (ValueError, TypeError):
            return raw
    if isinstance(raw, dict):
        currency = raw.get("currency", "")
        issuer = raw.get("issuer", "")
        if currency and issuer:
            return f"{currency}:{issuer}"
        if currency:
            return currency
    return str(raw)


def _clawback_relevant(asset_key: str, clawback_issuers: set[str]) -> bool:
    """Return True if asset has an issuer with clawback capability."""
    if ":" in asset_key:
        issuer = asset_key.split(":", 1)[1]
        return issuer in clawback_issuers
    return False


def build_amm_snapshot(
    raw_amm: dict[str, Any],
    ledger_index: int,
    clawback_issuers: set[str] | None = None,
) -> AMMSnapshot:
    """Build an AMMSnapshot from raw amm_info fixture data.

    Args:
        raw_amm: Raw dict from fixture (top-level or nested under "amm" key).
        ledger_index: Ledger index of the fixture data.
        clawback_issuers: Set of issuer accounts with clawback enabled.
    """
    limitations: list[str] = []
    capability_requirements: list[str] = [_AMM_CAPABILITY]
    clawback_issuers = clawback_issuers or set()

    if not is_capability_available(_AMM_CAPABILITY):
        limitations.append(
            f"AMM amendment ({_AMM_CAPABILITY}) is not ENABLED — AMM data is unavailable on mainnet"
        )

    # Unwrap nested "amm" key if present
    amm_data = raw_amm.get("amm", raw_amm)

    amount_a = amm_data.get("amount")
    amount_b = amm_data.get("amount2")

    if amount_a is None:
        limitations.append("missing 'amount' (Asset A) in AMM fixture")
    if amount_b is None:
        limitations.append("missing 'amount2' (Asset B) in AMM fixture")

    asset_a_key = _normalise_asset_key(amount_a) if amount_a is not None else "UNKNOWN_A"
    asset_b_key = _normalise_asset_key(amount_b) if amount_b is not None else "UNKNOWN_B"
    amm_account = amm_data.get("amm_account", "")

    trading_fee = amm_data.get("trading_fee")
    if trading_fee is None:
        limitations.append("missing 'trading_fee' in AMM fixture")

    lp_token = amm_data.get("lp_token")
    if lp_token is None:
        limitations.append("missing 'lp_token' in AMM fixture")

    reserves = {
        "asset_a_key": asset_a_key,
        "asset_b_key": asset_b_key,
        "amount_a_raw": amount_a,
        "amount_b_raw": amount_b,
    }

    # AMMClawback relevance check
    if is_capability_available(_AMM_CLAWBACK_CAPABILITY):
        if _clawback_relevant(asset_a_key, clawback_issuers) or _clawback_relevant(asset_b_key, clawback_issuers):
            capability_requirements.append(_AMM_CLAWBACK_CAPABILITY)
            limitations.append(
                "AMMClawback: issuer may claw back assets held in this AMM pool"
            )

    amm_id = _amm_id(asset_a_key, asset_b_key, amm_account)

    return AMMSnapshot(
        amm_id=amm_id,
        asset_a=asset_a_key,
        asset_b=asset_b_key,
        trading_fee=trading_fee,
        lp_token=lp_token,
        reserves=reserves,
        ledger_index=ledger_index,
        capability_requirements=capability_requirements,
        limitations=limitations,
    )
