from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import BacktestWindow
from .loaders import get_deterministic_id

class WindowBuilder:
    """Builds backtest windows from loaded records."""

    def build_windows_by_ledger(
        self, 
        dataset_id: str,
        records: List[Dict[str, Any]], 
        window_size_ledgers: int = 1000,
        window_type: str = "train"
    ) -> List[BacktestWindow]:
        """Group records into windows based on ledger index."""
        if not records:
            return []

        # Sort records by ledger index if available, otherwise observed_at
        sorted_records = sorted(
            records, 
            key=lambda x: (x.get("ledger_index", 0), x.get("observed_at", ""))
        )
        
        windows = []
        current_records = []
        start_ledger = None
        
        for record in sorted_records:
            ledger = record.get("ledger_index")
            if ledger is None:
                continue
                
            if start_ledger is None:
                start_ledger = ledger
            
            if ledger >= start_ledger + window_size_ledgers:
                # Close current window
                windows.append(self._create_window(dataset_id, current_records, window_type))
                current_records = []
                start_ledger = ledger
            
            current_records.append(record)
            
        if current_records:
            windows.append(self._create_window(dataset_id, current_records, window_type))
            
        return windows

    def _create_window(
        self, 
        dataset_id: str, 
        records: List[Dict[str, Any]], 
        window_type: str
    ) -> BacktestWindow:
        """Create a single BacktestWindow from a set of records."""
        if not records:
            return None
            
        ledgers = [r.get("ledger_index") for r in records if r.get("ledger_index") is not None]
        times = [r.get("observed_at") for r in records if r.get("observed_at") is not None]
        
        start_ledger = min(ledgers) if ledgers else None
        end_ledger = max(ledgers) if ledgers else None
        start_time = min(times) if times else None
        end_time = max(times) if times else None
        
        # Extract IDs
        asset_key_ids = list(set(r.get("asset_key") for r in records if r.get("asset_key")))
        candidate_ids = list(set(r.get("candidate_id") for r in records if r.get("candidate_id")))
        price_snapshot_ids = list(set(r.get("snapshot_id") for r in records if r.get("snapshot_id") and "price" in str(r.get("type", ""))))
        liquidity_snapshot_ids = list(set(r.get("snapshot_id") for r in records if r.get("snapshot_id") and "liquidity" in str(r.get("type", ""))))
        event_ids = list(set(r.get("event_id") for r in records if r.get("event_id")))

        window_id = get_deterministic_id([
            dataset_id,
            window_type,
            start_ledger,
            end_ledger,
            start_time,
            end_time,
            sorted(asset_key_ids),
            sorted(candidate_ids)
        ])

        return BacktestWindow(
            window_id=window_id,
            dataset_id=dataset_id,
            window_type=window_type,
            start_ledger=start_ledger,
            end_ledger=end_ledger,
            start_time=start_time,
            end_time=end_time,
            asset_key_ids=sorted(asset_key_ids),
            candidate_ids=sorted(candidate_ids),
            price_snapshot_ids=sorted(price_snapshot_ids),
            liquidity_snapshot_ids=sorted(liquidity_snapshot_ids),
            event_ids=sorted(event_ids)
        )
