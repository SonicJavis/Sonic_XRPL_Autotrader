import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

def calculate_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_phase30_report(report_dir: str) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any], List[str]]:
    path = Path(report_dir)
    jsonl_path = path / "reconciliation_records.jsonl"
    summary_path = path / "reconciliation_summary.json"
    limitations_path = path / "reconciliation_limitations.txt"
    
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Missing required Phase 30 file: {jsonl_path}")
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing required Phase 30 file: {summary_path}")
    if not limitations_path.exists():
        raise FileNotFoundError(f"Missing required Phase 30 file: {limitations_path}")
        
    records = []
    file_content = ""
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            file_content += line
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
            
    with open(summary_path, "r", encoding="utf-8") as f:
        summary_content = f.read()
        summary_data = json.loads(summary_content)
        file_content += summary_content
        
    limitations_data = []
    with open(limitations_path, "r", encoding="utf-8") as f:
        limits_content = f.read()
        file_content += limits_content
        for line in limits_content.splitlines():
            line = line.strip()
            if line.startswith("- "):
                limitations_data.append(line[2:])
                
    report_hash = calculate_hash(file_content)
    return records, report_hash, summary_data, limitations_data
