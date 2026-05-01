from dataclasses import dataclass, field
from typing import List, Optional, Dict
from decimal import Decimal
import hashlib
import json

@dataclass(frozen=True)
class MarketFixtureSource:
    source_id: str
    source_name: str
    source_type: str  # fixture | clio_export | ledger_export | manual_csv | synthetic_test
    created_at: str
    source_path: str
    source_hash: str
    limitations: List[str] = field(default_factory=list)
    prohibited_live_action: str = "LIVE TRADING STRICTLY FORBIDDEN"

@dataclass(frozen=True)
class AssetKey:
    issuer: Optional[str]
    currency_code: str
    normalized_currency: str
    asset_type: str  # xrp | issued_currency | mpt | unknown
    asset_key_id: str

    @staticmethod
    def generate_id(issuer: Optional[str], currency: str) -> str:
        # Sort and hash for determinism
        raw = f"{issuer or ''}:{currency.upper()}"
        return hashlib.sha256(raw.encode()).hexdigest()

@dataclass(frozen=True)
class PriceSnapshot:
    snapshot_id: str
    asset_key_id: str
    issuer: Optional[str]
    currency_code: str
    ledger_index: Optional[int]
    observed_at: Optional[str]
    price_xrp: Optional[str]
    price_usd: Optional[str]
    source_event_id: Optional[str]
    source_tx_hash: Optional[str]
    confidence: str  # low | medium | high
    limitations: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class LiquiditySnapshot:
    snapshot_id: str
    asset_key_id: str
    issuer: Optional[str]
    currency_code: str
    ledger_index: Optional[int]
    observed_at: Optional[str]
    amm_present: bool
    confidence: str  # low | medium | high
    amm_liquidity_xrp: Optional[str]
    orderbook_liquidity_xrp: Optional[str]
    estimated_exit_capacity_xrp: Optional[str]
    spread_pct: Optional[str]
    slippage_estimate_pct: Optional[str]
    source_event_ids: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class MarketTimeline:
    timeline_id: str
    asset_key_id: str
    price_snapshot_ids: List[str]
    liquidity_snapshot_ids: List[str]
    first_ledger_index: Optional[int]
    last_ledger_index: Optional[int]
    first_observed_at: Optional[str]
    last_observed_at: Optional[str]
    quality_score: int  # 0-100
    limitations: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class PaperMarkToMarketResult:
    result_id: str
    position_id: str
    campaign_id: str
    candidate_id: str
    asset_key_id: str
    entry_time: str
    entry_price_paper: Optional[str]
    latest_price_paper: Optional[str]
    exit_price_paper: Optional[str]
    unrealized_pnl_xrp: Optional[str]
    realized_pnl_xrp: Optional[str]
    pnl_pct: Optional[str]
    liquidity_exit_confidence: str  # low | medium | high
    outcome: str  # win | loss | breakeven | unknown
    unknown_reason: Optional[str]
    source_snapshot_ids: List[str]
    limitations: List[str]
    prohibited_live_action: str = "PROHIBITED LIVE ACTION"

@dataclass(frozen=True)
class FixtureQualityReport:
    quality_report_id: str
    total_price_snapshots: int
    total_liquidity_snapshots: int
    assets_covered: int
    missing_price_count: int
    missing_liquidity_count: int
    duplicate_snapshot_count: int
    out_of_order_count: int
    same_ticker_multi_issuer_count: int
    quality_score: int  # 0-100
    critical_issues: List[str]
    warnings: List[str]
    prohibited_live_action: str = "LIVE TRADING FORBIDDEN"
