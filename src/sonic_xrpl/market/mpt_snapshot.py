"""MPT snapshot builder — Phase 47.

Reads MPT holder fixture data. No live calls.
Capability check: MPTokensV1 amendment must be ENABLED.
"""

from __future__ import annotations

from typing import Any

from sonic_xrpl.market.models import MPTSnapshot
from sonic_xrpl.protocol.capability_matrix import is_capability_available

_MPT_CAPABILITY = "MPTokensV1"


def build_mpt_snapshot(
    raw_mpt_holders: dict[str, Any],
    mpt_id: str | None = None,
) -> MPTSnapshot:
    """Build an MPTSnapshot from raw MPT holders fixture data.

    Args:
        raw_mpt_holders: Raw dict from fixture.
        mpt_id: Explicit MPT issuance ID (overrides fixture value).
    """
    limitations: list[str] = []
    capability_requirements: list[str] = [_MPT_CAPABILITY]

    if not is_capability_available(_MPT_CAPABILITY):
        limitations.append(
            f"MPTokensV1 amendment ({_MPT_CAPABILITY}) is not ENABLED — MPT data is unavailable on mainnet"
        )

    resolved_mpt_id = (
        mpt_id
        or raw_mpt_holders.get("mpt_issuance_id", "")
    )

    if not resolved_mpt_id:
        limitations.append("mpt_issuance_id missing from fixture")
        resolved_mpt_id = "unknown"

    holders: list[dict[str, Any]] = raw_mpt_holders.get("holders", [])
    holder_count = len(holders)

    if holder_count == 0:
        limitations.append("no holder data in fixture")

    # Sample up to 10 holders — do not invent distribution
    holders_sample = holders[:10]

    return MPTSnapshot(
        mpt_id=resolved_mpt_id,
        holder_count=holder_count,
        holders_sample=holders_sample,
        capability_requirements=capability_requirements,
        limitations=limitations,
    )
