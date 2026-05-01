import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

def load_historical_runs(phase30_root: str, phase31_root: str) -> List[Dict[str, Any]]:
    # A run is identified by the timestamp folder. We assume the folder names are sortable timestamps (e.g. YYYYMMDD_HHMMSS)
    p30_path = Path(phase30_root)
    p31_path = Path(phase31_root)
    
    if not p30_path.exists():
        return []
        
    # Get all subdirectories (runs)
    p30_runs = sorted([d.name for d in p30_path.iterdir() if d.is_dir()])
    
    runs_data = []
    
    for run_name in p30_runs:
        run_dict = {
            "run_id": run_name,
            "reconciliation_records": [],
            "calibration_recommendations": [],
            "calibration_summary": None,
            "reconciliation_summary": None
        }
        
        # Load Phase 30
        p30_run_dir = p30_path / run_name
        rec_jsonl = p30_run_dir / "reconciliation_records.jsonl"
        rec_sum = p30_run_dir / "reconciliation_summary.json"
        
        if rec_jsonl.exists():
            with open(rec_jsonl, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        run_dict["reconciliation_records"].append(json.loads(line))
                        
        if rec_sum.exists():
            with open(rec_sum, "r", encoding="utf-8") as f:
                run_dict["reconciliation_summary"] = json.load(f)
                
        # Load Phase 31
        p31_run_dir = p31_path / run_name
        cal_jsonl = p31_run_dir / "calibration_recommendations.jsonl"
        cal_sum = p31_run_dir / "calibration_summary.json"
        
        if cal_jsonl.exists():
            with open(cal_jsonl, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        run_dict["calibration_recommendations"].append(json.loads(line))
                        
        if cal_sum.exists():
            with open(cal_sum, "r", encoding="utf-8") as f:
                run_dict["calibration_summary"] = json.load(f)
                
        runs_data.append(run_dict)
        
    return runs_data
