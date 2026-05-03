"""Immutable market snapshot dataclasses — Phase 47.

All models are frozen dataclasses. No mutable state. No live data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AssetType(str, Enum):
    """Type of XRPL asset."""
    XRP = "xrp"
    IOU = "iou"
    MPT = "mpt"
    UNKNOWN = "unknown"


class SnapshotRecommendation(str, Enum):
    """Quality-based recommendation for snapshot consumers."""
    USABLE_FOR_SIMULATION = "usable_for_simulation"
    USABLE_FOR_RESEARCH = "usable_for_research"
    INSUFFICIENT_DATA = "insufficient_data"
    REJECTED = "rejected"


@dataclass(frozen=True)
class AssetSnapshot:
    """Snapshot of a single XRPL asset."""
    asset_key: str
    asset_type: AssetType
    issuer: str | None
    currency: str | None
    mpt_id: str | None
    capability_requirements: list[str]
    risk_flags: list[str]
    limitations: list[str]


@dataclass(frozen=True)
class AMMSnapshot:
    """Snapshot of an XRPL AMM pool."""
    amm_id: str
    asset_a: str
    asset_b: str
    trading_fee: int | None       # in 1/100,000 units; 500 = 0.5%
    lp_token: dict[str, Any] | None
    reserves: dict[str, Any]
    ledger_index: int
    capability_requirements: list[str]
    limitations: list[str]

    @property
    def trading_fee_pct(self) -> float | None:
        """Return trading fee as percentage."""
        if self.trading_fee is None:
            return None
        return self.trading_fee / 100_000.0


@dataclass(frozen=True)
class OfferEntry:
    """A single offer in an orderbook."""
    account: str
    taker_gets: Any
    taker_pays: Any
    quality: str | None


@dataclass(frozen=True)
class OrderbookSnapshot:
    """Snapshot of an XRPL orderbook."""
    orderbook_id: str
    taker_gets: Any
    taker_pays: Any
    offers: list[OfferEntry]
    best_bid: str | None
    best_ask: str | None
    spread_bps: float | None
    depth_summary: dict[str, Any]
    ledger_index: int
    limitations: list[str]


@dataclass(frozen=True)
class AccountContext:
    """Account state from fixture data."""
    account: str
    ledger_index: int
    flags: int
    balance_drops: str
    owner_count: int
    sequence: int
    previous_txn_id: str | None
    limitations: list[str]


@dataclass(frozen=True)
class TrustlineContext:
    """Trust line state from fixture data."""
    account: str
    issuer: str
    currency: str
    balance: str
    limit: str
    flags: int
    no_ripple: bool
    freeze_state: str        # "none" | "frozen" | "deep_frozen"
    clawback_relevant: bool
    limitations: list[str]


@dataclass(frozen=True)
class MPTSnapshot:
    """MPT issuance holder snapshot."""
    mpt_id: str
    holder_count: int
    holders_sample: list[dict[str, Any]]
    capability_requirements: list[str]
    limitations: list[str]


@dataclass(frozen=True)
class MetadataSignal:
    """Signals extracted from a single transaction's metadata."""
    tx_hash: str
    tx_type: str
    ledger_index: int
    delivered_amount: Any
    affected_node_count: int
    balance_changes: list[dict[str, Any]]
    signal_flags: list[str]
    limitations: list[str]


@dataclass(frozen=True)
class SnapshotQuality:
    """Quality assessment of a market snapshot."""
    score: int                          # 0–100
    coverage: dict[str, bool]
    missing_sections: list[str]
    stale_sections: list[str]
    protocol_warnings: list[str]
    fixture_warnings: list[str]
    recommendation: SnapshotRecommendation


@dataclass(frozen=True)
class SnapshotManifest:
    """Provenance record for a market snapshot."""
    snapshot_id: str
    fixture_id: str
    source_hash: str
    generated_at: str
    builder_version: str
    input_paths: list[str]
    limitations: list[str]


@dataclass(frozen=True)
class MarketSnapshot:
    """Top-level market snapshot — all sections."""
    snapshot_id: str
    created_at: str
    fixture_id: str
    ledger_index: int
    network: str
    assets: list[AssetSnapshot]
    amms: list[AMMSnapshot]
    orderbooks: list[OrderbookSnapshot]
    accounts: list[AccountContext]
    trustlines: list[TrustlineContext]
    mpt_holders: list[MPTSnapshot]
    metadata_signals: list[MetadataSignal]
    capabilities: dict[str, bool]
    quality: SnapshotQuality
    limitations: list[str]
    source_hash: str
