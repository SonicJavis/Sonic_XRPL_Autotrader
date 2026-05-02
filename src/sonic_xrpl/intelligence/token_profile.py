"""Token profile — intelligence-layer token risk characterisation.

Intelligence does NOT execute (Architecture Rule #6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LiquidityTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class RiskFlag(str, Enum):
    CLAWBACK_ENABLED = "clawback_enabled"
    FREEZE_ENABLED = "freeze_enabled"
    LOW_LIQUIDITY = "low_liquidity"
    UNVERIFIED_ISSUER = "unverified_issuer"
    AMM_ONLY = "amm_only"
    MPT_ASSET = "mpt_asset"
    DEEP_FREEZE_POSSIBLE = "deep_freeze_possible"


@dataclass
class TokenProfile:
    """Risk profile for a single XRPL token."""

    currency: str
    issuer: str | None
    name: str | None = None
    trust_score: float = 0.5
    liquidity_tier: LiquidityTier = LiquidityTier.UNKNOWN
    risk_flags: list[RiskFlag] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_risk(self) -> bool:
        return len(self.risk_flags) > 2 or self.trust_score < 0.3

    @property
    def is_xrp(self) -> bool:
        return self.currency == "XRP" and self.issuer is None


def build_token_profile(
    currency: str,
    issuer: str | None,
    data: dict[str, Any] | None = None,
) -> TokenProfile:
    """Build a TokenProfile from raw ledger data.

    This is a minimal placeholder. Future phases will enrich this
    with live data from LedgerProvider.
    """
    data = data or {}
    flags: list[RiskFlag] = []

    if data.get("clawback_enabled"):
        flags.append(RiskFlag.CLAWBACK_ENABLED)
    if data.get("freeze_enabled"):
        flags.append(RiskFlag.FREEZE_ENABLED)

    return TokenProfile(
        currency=currency,
        issuer=issuer,
        name=data.get("name"),
        trust_score=float(data.get("trust_score", 0.5)),
        liquidity_tier=LiquidityTier(data.get("liquidity_tier", "unknown")),
        risk_flags=flags,
        metadata=data,
    )
