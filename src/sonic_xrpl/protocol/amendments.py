"""XRPL Amendment registry with known status as of Phase 45 research baseline.

Sources:
- https://xrpl.org/known-amendments.html
- https://github.com/XRPLF/rippled/releases
- https://xrpl.org/docs/references/protocol/transactions/pseudo-transaction-types/enableamendment/

Last checked: 2026-05-02 (offline research baseline, Phase 45).

NOTE: Amendment status on mainnet can change via validator voting. This registry
reflects the research baseline at Phase 45 creation. Do not make runtime decisions
from this file alone — query the live network for current amendment status.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AmendmentStatus(str, Enum):
    """Status of an XRPL amendment in the context of this codebase."""

    ENABLED = "enabled"
    OPEN_VOTING = "open_voting"
    FEATURE_GATED = "feature_gated"
    OBSOLETE = "obsolete"
    RESEARCH_ONLY = "research_only"


@dataclass(frozen=True)
class Amendment:
    """Metadata about a known XRPL amendment."""

    name: str
    status: AmendmentStatus
    xls_standard: str | None
    source_url: str
    architecture_impact: str
    enabled_by_default: bool
    last_checked: str


# ---------------------------------------------------------------------------
# Known amendments — sourced from xrpl.org/known-amendments.html
# ---------------------------------------------------------------------------
KNOWN_AMENDMENTS: dict[str, Amendment] = {
    # ── Enabled on mainnet ────────────────────────────────────────────────
    "AMM": Amendment(
        name="AMM",
        status=AmendmentStatus.ENABLED,
        xls_standard="XLS-30",
        source_url="https://xrpl.org/known-amendments.html#amm",
        architecture_impact="AMM pools can be queried; amm_info RPC available. "
        "Trading against AMMs is possible in paper/simulation modes.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    "AMMClawback": Amendment(
        name="AMMClawback",
        status=AmendmentStatus.ENABLED,
        xls_standard="XLS-73",
        source_url="https://xrpl.org/known-amendments.html#ammclawback",
        architecture_impact="Issuers with clawback enabled can claw from AMM pools. "
        "Risk layer must account for issuer clawback flags.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    "Clawback": Amendment(
        name="Clawback",
        status=AmendmentStatus.ENABLED,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html#clawback",
        architecture_impact="Token issuers may enable clawback on their assets. "
        "Intelligence layer must flag clawback-enabled tokens.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    "Credentials": Amendment(
        name="Credentials",
        status=AmendmentStatus.ENABLED,
        xls_standard="XLS-70",
        source_url="https://xrpl.org/known-amendments.html#credentials",
        architecture_impact="On-chain credential objects exist. Permissioned DEX "
        "may require credentials. Feature-gated in architecture.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    "DID": Amendment(
        name="DID",
        status=AmendmentStatus.ENABLED,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html#did",
        architecture_impact="Decentralised Identity objects on-chain. "
        "Research-only for trading use cases.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    "DeepFreeze": Amendment(
        name="DeepFreeze",
        status=AmendmentStatus.ENABLED,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html#deepfreeze",
        architecture_impact="Issuers can deep-freeze trust lines. "
        "Risk layer must check freeze status of trust lines.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    "ExpandedSignerList": Amendment(
        name="ExpandedSignerList",
        status=AmendmentStatus.ENABLED,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html#expandedsignerlist",
        architecture_impact="Larger multisig signer lists supported. "
        "Relevant only if multisig wallet construction is ever enabled.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    "MPTokensV1": Amendment(
        name="MPTokensV1",
        status=AmendmentStatus.ENABLED,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html#mptokensv1",
        architecture_impact="Multi-Purpose Tokens (MPTs) are available. "
        "Intelligence layer should profile MPT issuances.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    "PriceOracle": Amendment(
        name="PriceOracle",
        status=AmendmentStatus.ENABLED,
        xls_standard="XLS-47",
        source_url="https://xrpl.org/known-amendments.html#priceoracle",
        architecture_impact="On-chain price oracle objects are available. "
        "Intelligence layer can ingest oracle prices.",
        enabled_by_default=True,
        last_checked="2026-05-02",
    ),
    # ── Feature-gated / open voting ───────────────────────────────────────
    "LendingProtocol": Amendment(
        name="LendingProtocol",
        status=AmendmentStatus.FEATURE_GATED,
        xls_standard="XLS-66",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Lending vaults not yet available on mainnet. "
        "Feature gate required before any lending logic is built.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    "SingleAssetVault": Amendment(
        name="SingleAssetVault",
        status=AmendmentStatus.FEATURE_GATED,
        xls_standard="XLS-65",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Single-asset vaults not on mainnet. Feature-gated.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    "PermissionedDEX": Amendment(
        name="PermissionedDEX",
        status=AmendmentStatus.FEATURE_GATED,
        xls_standard="XLS-81",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Permissioned DEX requires Credentials. Not on mainnet.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    "PermissionedDomains": Amendment(
        name="PermissionedDomains",
        status=AmendmentStatus.FEATURE_GATED,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html",
        architecture_impact="Domain-scoped permissioned trading. Not on mainnet.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    "TokenEscrow": Amendment(
        name="TokenEscrow",
        status=AmendmentStatus.FEATURE_GATED,
        xls_standard="XLS-85",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Token-backed escrow not on mainnet. Feature-gated.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    # ── Obsolete — do NOT build against ──────────────────────────────────
    "Batch": Amendment(
        name="Batch",
        status=AmendmentStatus.OBSOLETE,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html",
        architecture_impact="OBSOLETE. Do not reference in new code.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    "PermissionDelegation": Amendment(
        name="PermissionDelegation",
        status=AmendmentStatus.OBSOLETE,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html",
        architecture_impact="OBSOLETE. Do not reference in new code.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    "fixBatchInnerSigs": Amendment(
        name="fixBatchInnerSigs",
        status=AmendmentStatus.OBSOLETE,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html",
        architecture_impact="OBSOLETE. Do not reference in new code.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    # ── Research-only ─────────────────────────────────────────────────────
    "HooksOnMainnet": Amendment(
        name="HooksOnMainnet",
        status=AmendmentStatus.RESEARCH_ONLY,
        xls_standard=None,
        source_url="https://xrpl.org/known-amendments.html",
        architecture_impact="Hooks are NOT on XRPL mainnet. Xahau only. "
        "No Hooks logic in V2 unless explicitly requested.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    "XahauHooks": Amendment(
        name="XahauHooks",
        status=AmendmentStatus.RESEARCH_ONLY,
        xls_standard=None,
        source_url="https://xahau.network/docs",
        architecture_impact="Xahau-specific. Separate chain from XRPL mainnet. "
        "Research-only provider abstraction may support Xahau in future.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
    "SmartContractsXLS101": Amendment(
        name="SmartContractsXLS101",
        status=AmendmentStatus.RESEARCH_ONLY,
        xls_standard="XLS-101",
        source_url="https://github.com/XRPLF/XRPL-Standards/discussions",
        architecture_impact="Smart contracts proposal. Research-only. "
        "Not available on mainnet.",
        enabled_by_default=False,
        last_checked="2026-05-02",
    ),
}


def get_amendment(name: str) -> Amendment:
    """Return amendment metadata by name."""
    if name not in KNOWN_AMENDMENTS:
        raise KeyError(f"Unknown amendment: {name!r}")
    return KNOWN_AMENDMENTS[name]


def is_amendment_enabled(name: str) -> bool:
    """Return True if the amendment is marked ENABLED in the research baseline."""
    try:
        return KNOWN_AMENDMENTS[name].status == AmendmentStatus.ENABLED
    except KeyError:
        return False


def get_obsolete_amendments() -> list[str]:
    """Return names of all OBSOLETE amendments."""
    return [
        name
        for name, a in KNOWN_AMENDMENTS.items()
        if a.status == AmendmentStatus.OBSOLETE
    ]


def get_research_only_amendments() -> list[str]:
    """Return names of all RESEARCH_ONLY amendments."""
    return [
        name
        for name, a in KNOWN_AMENDMENTS.items()
        if a.status == AmendmentStatus.RESEARCH_ONLY
    ]
