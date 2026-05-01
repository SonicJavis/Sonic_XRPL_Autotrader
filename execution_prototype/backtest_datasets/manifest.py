from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import BacktestDatasetManifest, BacktestWindow
from .loaders import get_deterministic_id

class ManifestBuilder:
    """Builds the dataset manifest."""

    def build_manifest(
        self,
        dataset_name: str,
        dataset_version: str,
        sources: List[str],
        windows: List[BacktestWindow],
        all_records: List[Dict[str, Any]],
        quality_score: int,
        limitations: List[str]
    ) -> BacktestDatasetManifest:
        
        asset_keys = set(r.get("asset_key") for r in all_records if r.get("asset_key"))
        candidates = set(r.get("candidate_id") for r in all_records if r.get("candidate_id"))
        prices = [r for r in all_records if "price" in str(r.get("type", ""))]
        liquidity = [r for r in all_records if "liquidity" in str(r.get("type", ""))]
        
        ledgers = [r.get("ledger_index") for r in all_records if r.get("ledger_index") is not None]
        times = [r.get("observed_at") for r in all_records if r.get("observed_at") is not None]
        
        ledger_range = f"{min(ledgers)} - {max(ledgers)}" if ledgers else "Unknown"
        time_range = f"{min(times)} - {max(times)}" if times else "Unknown"
        
        dataset_id = get_deterministic_id([
            dataset_name,
            dataset_version,
            sorted(sources),
            len(all_records),
            ledger_range,
            time_range
        ])
        
        # Calculate dataset hash (stable representation of all windows/sources)
        dataset_hash = get_deterministic_id([dataset_id, [w.window_id for w in windows]])

        return BacktestDatasetManifest(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            created_at=datetime.utcnow().isoformat(),
            source_ids=sources,
            window_ids=[w.window_id for w in windows],
            asset_count=len(asset_keys),
            candidate_count=len(candidates),
            price_snapshot_count=len(prices),
            liquidity_snapshot_count=len(liquidity),
            time_range_summary=time_range,
            ledger_range_summary=ledger_range,
            split_strategy="chronological_60_20_20",
            quality_score=quality_score,
            dataset_hash=dataset_hash,
            limitations=limitations
        )
