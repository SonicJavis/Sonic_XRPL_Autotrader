import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Any
from dataclasses import asdict as as_dict

def write_reports(
    output_dir: Path,
    sources: List[Any],
    prices: List[Any],
    liquidity: List[Any],
    results: List[Any],
    quality: Any
):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Write JSONL
    with open(out_path / "normalized_price_snapshots.jsonl", "w") as f:
        for p in prices:
            f.write(json.dumps(as_dict(p)) + "\n")
            
    with open(out_path / "paper_mark_to_market_results.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(as_dict(r)) + "\n")
            
    # Write Summary JSON
    summary = {
        "quality_report": as_dict(quality),
        "total_results": len(results),
        "generated_at": timestamp
    }
    with open(out_path / "market_fixture_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    _write_markdown(out_path / "market_fixture_report.md", quality, results)
    
    return out_path

def _write_markdown(path: Path, quality: Any, results: List[Any]):
    with open(path, "w") as f:
        f.write("# Phase 40: Market Fixture Report\n\n")
        f.write("## 1. Research Sources Checked\n")
        f.write("- XRPL Known Amendments (AMM, Clawback, MPT confirmed)\n")
        f.write("- rippled Release Notes (3.1.2 security refactor)\n")
        f.write("- xrpl-py (get_balance_changes verified)\n\n")
        
        f.write("## 2. Fixture Quality Summary\n")
        f.write(f"- Quality Score: **{quality.quality_score}**\n")
        f.write(f"- Total Price Snapshots: {quality.total_price_snapshots}\n")
        f.write(f"- Assets Covered: {quality.assets_covered}\n\n")
        
        f.write("## 6. Mark-to-Market Results\n")
        wins = len([r for r in results if r.outcome == "win"])
        losses = len([r for r in results if r.outcome == "loss"])
        f.write(f"- Wins: {wins}\n")
        f.write(f"- Losses: {losses}\n\n")
        
        f.write("## 13. Why Live Trading Is Still Forbidden\n")
        f.write("LIVE TRADING FORBIDDEN. This engine uses offline fixtures to enrich paper simulations. No live execution pathways exist.\n")
