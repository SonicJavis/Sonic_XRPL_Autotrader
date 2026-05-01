from typing import List, Dict, Any, Tuple
from .models import BacktestWindow

class DatasetSplitter:
    """Splits records or windows into train/validation/test sets."""

    def split_chronologically(
        self, 
        records: List[Dict[str, Any]], 
        train_pct: float = 0.6, 
        val_pct: float = 0.2, 
        test_pct: float = 0.2
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Split records chronologically without shuffling."""
        if not records:
            return {"train": [], "validation": [], "test": [], "replay": [], "holdout": []}

        # Sort by ledger index then time
        sorted_records = sorted(
            records, 
            key=lambda x: (x.get("ledger_index", 0), x.get("observed_at", ""))
        )
        
        total = len(sorted_records)
        train_end = int(total * train_pct)
        val_end = train_end + int(total * val_pct)
        
        return {
            "train": sorted_records[:train_end],
            "validation": sorted_records[train_end:val_end],
            "test": sorted_records[val_end:],
            "replay": [],  # Optional
            "holdout": []  # Optional
        }

    def split_windows(
        self,
        windows: List[BacktestWindow],
        train_pct: float = 0.6,
        val_pct: float = 0.2,
        test_pct: float = 0.2
    ) -> Dict[str, List[BacktestWindow]]:
        """Split windows chronologically."""
        if not windows:
            return {"train": [], "validation": [], "test": []}

        # Windows are already deterministic, but let's ensure order
        sorted_windows = sorted(
            windows,
            key=lambda w: (w.start_ledger if w.start_ledger is not None else 0, w.start_time if w.start_time is not None else "")
        )

        total = len(sorted_windows)
        train_end = int(total * train_pct)
        val_end = train_end + int(total * val_pct)

        # Update window types
        split_windows = {
            "train": [],
            "validation": [],
            "test": []
        }

        for i, window in enumerate(sorted_windows):
            if i < train_end:
                split_windows["train"].append(self._update_window_type(window, "train"))
            elif i < val_end:
                split_windows["validation"].append(self._update_window_type(window, "validation"))
            else:
                split_windows["test"].append(self._update_window_type(window, "test"))

        return split_windows

    def _update_window_type(self, window: BacktestWindow, new_type: str) -> BacktestWindow:
        """Create a copy of the window with a new type."""
        from dataclasses import replace
        return replace(window, window_type=new_type)
