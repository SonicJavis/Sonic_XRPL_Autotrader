from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass(frozen=True)
class BacktestDatasetSource:
    source_id: str  # Deterministic hash
    source_type: str  # discovery_report | market_fixtures | adapter_export | phase40_report | manual_fixture
    source_path: str
    source_hash: str
    records_loaded: int
    limitations: List[str] = field(default_factory=list)
    prohibited_live_action: str = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."

@dataclass(frozen=True)
class BacktestWindow:
    window_id: str  # Deterministic hash
    dataset_id: str
    window_type: str  # train | validation | test | replay | holdout
    start_ledger: Optional[int] = None
    end_ledger: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    asset_key_ids: List[str] = field(default_factory=list)
    candidate_ids: List[str] = field(default_factory=list)
    price_snapshot_ids: List[str] = field(default_factory=list)
    liquidity_snapshot_ids: List[str] = field(default_factory=list)
    event_ids: List[str] = field(default_factory=list)
    quality_score: int = 100
    limitations: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class BacktestDatasetManifest:
    dataset_id: str  # Deterministic hash
    dataset_name: str
    dataset_version: str
    created_at: str
    source_ids: List[str]
    window_ids: List[str]
    asset_count: int
    candidate_count: int
    price_snapshot_count: int
    liquidity_snapshot_count: int
    time_range_summary: str
    ledger_range_summary: str
    split_strategy: str
    quality_score: int
    dataset_hash: str
    limitations: List[str] = field(default_factory=list)
    prohibited_live_action: str = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."

@dataclass(frozen=True)
class BacktestDatasetQualityReport:
    quality_report_id: str  # Deterministic hash
    dataset_id: str
    total_records: int
    valid_records: int
    invalid_records: int
    missing_price_count: int
    missing_liquidity_count: int
    missing_metadata_count: int
    same_ticker_multi_issuer_count: int
    out_of_order_count: int
    future_leakage_count: int
    duplicate_record_count: int
    unsupported_batch_context_count: int
    xahau_hook_context_count: int
    quality_score: int
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    prohibited_live_action: str = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."

@dataclass(frozen=True)
class DatasetExportSummary:
    export_id: str  # Deterministic hash
    dataset_id: str
    output_path: str
    files_written: List[str]
    records_written: int
    append_only: bool = True
    compatible_with_phase37: bool = True
    compatible_with_phase40: bool = True
    compatible_with_phase41: bool = True
    limitations: List[str] = field(default_factory=list)
