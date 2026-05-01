import argparse
import sys
import json
from pathlib import Path
from .loaders import load_price_snapshots, load_liquidity_snapshots
from .quality_checks import run_quality_checks
from .mark_to_market import enrich_paper_positions
from .report_writer import write_reports

def main():
    parser = argparse.ArgumentParser(description="Phase 40 Market Fixture Engine")
    parser.add_argument("--market-fixtures", required=True, help="Path to market fixtures dir")
    parser.add_argument("--phase36-report", required=True, help="Path to Phase 36 report dir")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Do not write outputs")
    
    args = parser.parse_args()
    
    fixtures_dir = Path(args.market_fixtures)
    p36_dir = Path(args.phase36_report)
    out_dir = Path(args.output_dir)
    
    if not fixtures_dir.exists():
        print(f"Error: Market fixtures directory not found: {fixtures_dir}")
        sys.exit(1)
        
    # 1. Load fixtures
    prices = load_price_snapshots(fixtures_dir / "prices.jsonl")
    liquidity = load_liquidity_snapshots(fixtures_dir / "liquidity.jsonl")
    
    # 2. Quality checks
    quality = run_quality_checks(prices, liquidity)
    
    # 3. Mark-to-market
    # Load paper positions from Phase 36
    positions = []
    pos_file = p36_dir / "paper_positions.jsonl"
    if pos_file.exists():
        with open(pos_file, "r") as f:
            for line in f:
                if line.strip():
                    positions.append(json.loads(line))
                    
    results = enrich_paper_positions(positions, prices, liquidity, "campaign_manual")
    
    # 4. Reports
    if not args.dry_run:
        final_path = write_reports(out_dir, [], [], [], results, quality)
        print(f"Phase 40 completion successful. Reports saved to: {final_path}")
    else:
        print("Dry run successful. No outputs written.")

if __name__ == "__main__":
    main()
