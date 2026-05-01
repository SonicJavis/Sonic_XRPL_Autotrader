from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib
import json

@dataclass(frozen=True)
class DataAdapterConfig:
    adapter_id: str
    source_type: str  # fixture | clio | xrpl_rpc | firstledger | manual
    endpoint: Optional[str] = None
    network_read_enabled: bool = False
    ledger_min: Optional[int] = None
    ledger_max: Optional[int] = None
    account: Optional[str] = None
    issuer: Optional[str] = None
    currency_code: Optional[str] = None
    max_records: Optional[int] = 1000
    max_pages: Optional[int] = 10
    rate_limit_per_minute: Optional[int] = 60
    strict: bool = False
    dry_run: bool = True
    prohibited_live_action: str = "LIVE TRADING STRICTLY FORBIDDEN"

@dataclass(frozen=True)
class RawSourceRecord:
    record_id: str
    source_type: str
    record_type: str  # transaction | ledger | account_lines | amm_info | firstledger_trade | manual_fixture
    ledger_index: Optional[int]
    tx_hash: Optional[str]
    observed_at: Optional[str]
    raw_payload_hash: str
    payload: Dict[str, Any]
    limitations: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class FixtureExportRecord:
    export_id: str
    source_record_ids: List[str]
    fixture_type: str  # price | liquidity | amm_snapshot | orderbook_snapshot | asset_metadata
    asset_key: str
    issuer: Optional[str]
    currency_code: str
    ledger_index: Optional[int]
    observed_at: Optional[str]
    payload: Dict[str, Any]
    confidence: str  # low | medium | high
    limitations: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class AdapterRunSummary:
    run_id: str
    source_type: str
    network_read_enabled: bool
    dry_run: bool
    records_read: int
    fixtures_written: int
    quality_score: int  # 0-100
    warnings: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    prohibited_live_action: str = "LIVE TRADING FORBIDDEN"
