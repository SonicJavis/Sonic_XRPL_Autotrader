from typing import List, Dict, Any, Optional
from .models import BacktestWindow

class LeakageChecker:
    """Checks for future leakage in datasets."""

    def check_future_leakage(self, records: List[Dict[str, Any]]) -> List[str]:
        """Detect if records contain future data relevant to past decisions."""
        issues = []
        
        # Sort records to establish "time"
        sorted_records = sorted(
            records, 
            key=lambda x: (x.get("ledger_index", 0), x.get("observed_at", ""))
        )
        
        # Track the latest "known" data for each asset
        # If we see a record that uses a "future" snapshot, it's leakage.
        # However, the dataset itself is a collection of snapshots.
        # The check is: Does a 'decision' event (like a candidate score)
        # reference a snapshot ID that hasn't appeared yet in the chronological stream?
        
        known_snapshots = set()
        for record in sorted_records:
            rtype = record.get("type", "")
            
            # If it's a snapshot, it's now "known"
            if "snapshot" in rtype:
                known_snapshots.add(record.get("snapshot_id"))
            
            # If it's a decision/candidate, check its referenced snapshots
            if "candidate" in rtype or "score" in rtype:
                referenced = record.get("referenced_snapshots", [])
                for ref_id in referenced:
                    if ref_id not in known_snapshots:
                        issues.append(
                            f"Future Leakage: Decision at ledger {record.get('ledger_index')} "
                            f"references future snapshot {ref_id}"
                        )
        
        return issues

    def check_outcome_leakage(self, features: Dict[str, Any], labels: Dict[str, Any]) -> List[str]:
        """Ensure labels are not present in the features dictionary."""
        issues = []
        feature_keys = set(features.keys())
        label_keys = set(labels.keys())
        
        overlap = feature_keys.intersection(label_keys)
        if overlap:
            issues.append(f"Outcome Leakage: Features contain label keys: {overlap}")
            
        return issues
