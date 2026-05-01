import argparse
import sys
from datetime import datetime, timezone

from execution_prototype.discovery.sources import load_fixture_transactions
from execution_prototype.discovery.xrpl_reader import process_transactions
from execution_prototype.discovery.candidate_builder import build_candidates
from execution_prototype.discovery.models import DiscoverySummary
from execution_prototype.discovery.report_writer import write_reports

SCHEMA_VERSION = "1.0.0"

def main():
    parser = argparse.ArgumentParser(description="Phase 34 XRPL Meme Discovery Engine")
    parser.add_argument("--source", required=True, choices=["fixture", "xrpl"], help="Data source mode")
    parser.add_argument("--input", help="Path to fixture file/directory")
    parser.add_argument("--ledger-window", type=int, help="Ledger window for XRPL mode")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    txs = []
    if args.source == "fixture":
        if not args.input:
            print("Error: --input is required for fixture mode.")
            sys.exit(1)
        txs = load_fixture_transactions(args.input)
    elif args.source == "xrpl":
        print("Warning: Live XRPL connection not yet implemented in Phase 34 prototype. Failing gracefully.")
        print("Please use --source fixture.")
        sys.exit(0)
        
    events = process_transactions(txs)
    candidates = build_candidates(events)
    
    bands = {"ignore": 0, "watch": 0, "review": 0, "high_attention": 0}
    for c in candidates:
        bands[c.score_band] += 1
        
    summary = DiscoverySummary(
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_events_processed=len(events),
        total_candidates_found=len(candidates),
        candidates_by_band=bands,
        safety_statement="This is a read-only discovery engine. It produces advisory candidates based on ledger truth. No trading automation or submission capabilities exist."
    )
    
    write_reports(args.output_dir, events, candidates, summary)
    
    print(f"Discovery complete. Processed {len(events)} events, found {len(candidates)} candidates.")
    sys.exit(0)

if __name__ == "__main__":
    main()
