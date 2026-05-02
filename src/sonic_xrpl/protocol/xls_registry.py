"""XLS (XRPL Ledger Standard) Registry for Phase 45.

Sources:
- https://github.com/XRPLF/XRPL-Standards
- Individual XLS discussion threads

Status values reflect whether the standard is implemented on mainnet,
in open voting, or research-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class XLSStatus(str, Enum):
    MAINNET = "mainnet"
    DEVNET = "devnet"
    OPEN_VOTING = "open_voting"
    DRAFT = "draft"
    RESEARCH = "research"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class XLSStandard:
    """Metadata for a single XLS standard."""

    number: int
    name: str
    status: XLSStatus
    description: str
    source_url: str
    architecture_impact: str


XLS_REGISTRY: dict[str, XLSStandard] = {
    "XLS-30": XLSStandard(
        number=30,
        name="AMM",
        status=XLSStatus.MAINNET,
        description="Automated Market Maker — native liquidity pools on XRPL.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions/78",
        architecture_impact="AMM pools queryable; paper trading can simulate AMM fills.",
    ),
    "XLS-47": XLSStandard(
        number=47,
        name="Price Oracles",
        status=XLSStatus.MAINNET,
        description="On-chain price oracle objects for publishing external prices.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions/119",
        architecture_impact="Intelligence layer can ingest oracle price objects.",
    ),
    "XLS-65": XLSStandard(
        number=65,
        name="Single Asset Vault",
        status=XLSStatus.DRAFT,
        description="Single-asset yield vaults (lending infrastructure).",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Feature-gated; not on mainnet as of Phase 45.",
    ),
    "XLS-66": XLSStandard(
        number=66,
        name="Lending Protocol",
        status=XLSStatus.DRAFT,
        description="Lending and borrowing protocol using XLS-65 vaults.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Feature-gated; not on mainnet as of Phase 45.",
    ),
    "XLS-70": XLSStandard(
        number=70,
        name="Credentials",
        status=XLSStatus.MAINNET,
        description="On-chain credential objects for identity and compliance.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Needed for PermissionedDEX. Risk layer should check.",
    ),
    "XLS-73": XLSStandard(
        number=73,
        name="AMMClawback",
        status=XLSStatus.MAINNET,
        description="Allows token issuers to clawback from AMM pools.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Risk layer must check issuer clawback flag on AMM assets.",
    ),
    "XLS-81": XLSStandard(
        number=81,
        name="Permissioned DEX",
        status=XLSStatus.DRAFT,
        description="DEX access restricted by on-chain credentials.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Feature-gated. Depends on XLS-70. Not on mainnet.",
    ),
    "XLS-85": XLSStandard(
        number=85,
        name="Token Escrow",
        status=XLSStatus.DRAFT,
        description="Escrow for issued tokens (not just XRP).",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Feature-gated. Not on mainnet as of Phase 45.",
    ),
    "XLS-87": XLSStandard(
        number=87,
        name="Token Pre-Authorization",
        status=XLSStatus.RESEARCH,
        description="Allow-list based pre-authorisation for token receipt.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Research-only. Not on mainnet.",
    ),
    "XLS-91": XLSStandard(
        number=91,
        name="Beneficiary",
        status=XLSStatus.RESEARCH,
        description="Account beneficiary designation for inheritance use cases.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Research-only.",
    ),
    "XLS-92": XLSStandard(
        number=92,
        name="Sub-Accounts",
        status=XLSStatus.RESEARCH,
        description="Sub-account structure within a parent account.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Research-only. Significant wallet-architecture impact if adopted.",
    ),
    "XLS-101": XLSStandard(
        number=101,
        name="Smart Contracts",
        status=XLSStatus.RESEARCH,
        description="EVM-compatible smart contract layer proposal.",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Research-only. Not on mainnet. Major future impact if adopted.",
    ),
}


def get_xls(key: str) -> XLSStandard:
    """Return XLS standard metadata by key (e.g. 'XLS-30')."""
    if key not in XLS_REGISTRY:
        raise KeyError(f"Unknown XLS standard: {key!r}")
    return XLS_REGISTRY[key]
