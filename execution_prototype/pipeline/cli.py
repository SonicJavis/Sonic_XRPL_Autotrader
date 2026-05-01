import argparse
import sys
from pathlib import Path
from execution_prototype.paper_operator.loaders import load_discovery_candidates, load_drift_warnings
from execution_prototype.paper_operator.portfolio import initialize_ledger
from execution_prototype.paper_operator.paper_executor import execute_cycle
from execution_prototype.paper_operator.report_writer import write_decisions, write_ledger, write_history
from execution_prototype.paper_review.cli import analyze_performance, write_reports as write_review_reports

def main():
    parser = argparse.ArgumentParser(description="Phase 36 Paper Operator Pipeline")
    parser.add_argument("--discovery-report", required=True, help="Path to discovery report directory")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--duration-days", type=int, default=7)
    parser.add_argument("--starting-balance-xrp", type=float, default=1000.0)
    parser.add_argument("--run-review", action="store_true")
    
    args = parser.parse_args()
    
    discovery_dir = Path(args.discovery_report)
    out_dir = Path(args.output_dir)
    
    candidates = load_discovery_candidates(discovery_dir)
    drift_warnings = load_drift_warnings(discovery_dir)
    
    ledger = initialize_ledger(
        campaign_id="c_001", 
        starting_balance=args.starting_balance_xrp,
        max_positions=5
    )
    
    # Mock price feed
    price_feed = {c.get("candidate_id"): 0.015 for c in candidates}
    
    # Execute Cycle
    final_ledger, decisions, history = execute_cycle(
        candidates=candidates,
        drift_warnings=drift_warnings,
        ledger=ledger,
        price_feed=price_feed
    )
    
    write_decisions(out_dir, decisions)
    write_ledger(out_dir, final_ledger)
    write_history(out_dir, history)
    
    if args.run_review:
        review = analyze_performance(final_ledger.campaign_id, history)
        write_review_reports(str(out_dir), history, review)
        
    print(f"Paper Operator Pipeline completed. Output saved to {out_dir}")
    sys.exit(0)

if __name__ == "__main__":
    main()
