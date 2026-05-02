"""Asset representation for XRPL V2.

XRPL has two kinds of assets:
- XRP (native, no issuer)
- Issued currencies (currency code + issuer account)
- MPTokens (MPT issuance ID)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class XRPAmount:
    """Native XRP amount in drops (1 XRP = 1,000,000 drops)."""

    drops: int

    @classmethod
    def from_xrp(cls, xrp: float) -> "XRPAmount":
        return cls(drops=int(xrp * 1_000_000))

    @property
    def xrp(self) -> float:
        return self.drops / 1_000_000


@dataclass(frozen=True)
class IssuedCurrency:
    """An XRPL issued currency (currency code + issuer)."""

    currency: str
    issuer: str

    def __str__(self) -> str:
        return f"{self.currency}.{self.issuer[:8]}..."


@dataclass(frozen=True)
class IssuedAmount:
    """An amount of issued currency."""

    currency: IssuedCurrency
    value: str  # String to preserve precision


@dataclass(frozen=True)
class MPToken:
    """A Multi-Purpose Token issuance."""

    mpt_issuance_id: str
    issuer: str


# Union type for any XRPL asset
Asset = XRPAmount | IssuedCurrency | MPToken


XRP = "XRP"
