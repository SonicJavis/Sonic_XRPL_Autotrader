import json
import csv
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from execution_prototype.reconciliation.models import ReconciliationRecord

def write_reports(records: List[ReconciliationRecord], output_dir: str, format: str = "both") -> Dict[str, Any]:
    # Create timestamped folder
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir) / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    jsonl_path = out_path / "reconciliation_records.jsonl"
    csv_path = out_path / "reconciliation_records.csv"
    summary_path = out_path / "reconciliation_summary.json"
    limitations_path = out_path / "reconciliation_limitations.txt"
    
    # Calculate Summary metrics
    total_compared = len(records)
    exact_match_count = sum(1 for r in records if r.match_status == "EXACT")
    partial_match_count = sum(1 for r in records if r.match_status not in ["EXACT", "AMBIGUOUS_MATCH"])
    insufficient_data_count = sum(1 for r in records if "INSUFFICIENT_REALITY_DATA" in r.drift_flags or "INSUFFICIENT_SIMULATION_DATA" in r.drift_flags)
    mismatch_count = total_compared - exact_match_count - partial_match_count
    
    status_matches = sum(1 for r in records if r.status_match)
    status_match_rate = (status_matches / total_compared) if total_compared > 0 else 0.0
    
    fee_deltas = [r.fee_delta_drops for r in records if r.fee_delta_drops is not None]
    avg_fee_delta_drops = sum(fee_deltas) / len(fee_deltas) if fee_deltas else 0.0
    
    val_deltas = [r.validation_ledger_delta for r in records if r.validation_ledger_delta is not None]
    avg_validation_ledger_delta = sum(val_deltas) / len(val_deltas) if val_deltas else 0.0
    
    drift_flag_counts = {}
    top_limitations_counts = {}
    
    for r in records:
        for flag in r.drift_flags:
            drift_flag_counts[flag] = drift_flag_counts.get(flag, 0) + 1
        for limit in r.limitations:
            top_limitations_counts[limit] = top_limitations_counts.get(limit, 0) + 1
            
    # Sort limitations
    top_limitations = [k for k, v in sorted(top_limitations_counts.items(), key=lambda item: item[1], reverse=True)]
    
    summary = {
        "total_compared": total_compared,
        "exact_match_count": exact_match_count,
        "partial_match_count": partial_match_count,
        "mismatch_count": mismatch_count,
        "insufficient_data_count": insufficient_data_count,
        "status_match_rate": status_match_rate,
        "avg_fee_delta_drops": avg_fee_delta_drops,
        "avg_validation_ledger_delta": avg_validation_ledger_delta,
        "drift_flag_counts": drift_flag_counts,
        "top_limitations": top_limitations
    }
    
    # Write Summary
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    # Write Limitations
    with open(limitations_path, "w", encoding="utf-8") as f:
        f.write("RECONCILIATION LIMITATIONS\n")
        f.write("==========================\n\n")
        for lim in top_limitations:
            f.write(f"- {lim} ({top_limitations_counts[lim]} occurrences)\n")
            
    # Write JSONL
    if format in ["jsonl", "both"]:
        with open(jsonl_path, "a", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r.to_dict()) + "\n")
                
    # Write CSV
    if format in ["csv", "both"] and records:
        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            # Flatten lists to comma-separated strings for CSV
            fieldnames = list(records[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                d = r.to_dict()
                d["drift_flags"] = "|".join(d["drift_flags"])
                d["limitations"] = "|".join(d["limitations"])
                d["notes"] = "|".join(d["notes"])
                writer.writerow(d)
                
    return {
        "summary": summary,
        "files": [str(p) for p in [summary_path, limitations_path, jsonl_path, csv_path] if p.exists()]
    }
