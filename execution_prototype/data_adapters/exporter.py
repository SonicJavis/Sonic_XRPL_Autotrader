import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Any
from dataclasses import asdict

def export_fixtures(
    output_dir: Path,
    raw_records: List[Any],
    fixtures: List[Any],
    summary: Any
):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Write Raw Records
    with open(out_path / "raw_source_records.jsonl", "w") as f:
        for r in raw_records:
            f.write(json.dumps(asdict(r)) + "\n")
            
    # Write Normalized Fixtures (Phase 40 compatible)
    # Group by fixture type
    prices = [f for f in fixtures if f.fixture_type == "price"]
    liquidity = [f for f in fixtures if f.fixture_type == "liquidity"]
    
    if prices:
        with open(out_path / "prices.jsonl", "w") as f:
            for p in prices:
                # Map to Phase 40 PriceSnapshot shape
                f.write(json.dumps(p.payload) + "\n")
                
    if liquidity:
        with open(out_path / "liquidity.jsonl", "w") as f:
            for l in liquidity:
                # Map to Phase 40 LiquiditySnapshot shape
                f.write(json.dumps(l.payload) + "\n")
                
    # Write Summary
    with open(out_path / "adapter_run_summary.json", "w") as f:
        json.dump(asdict(summary), f, indent=2)
        
    return out_path
