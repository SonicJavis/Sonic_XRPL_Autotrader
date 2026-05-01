import argparse
import sys
from pathlib import Path

from execution_prototype.risk_governor.loaders import (
    load_early_warnings, load_meme_candidates, load_paper_review,
    load_paper_decisions, load_paper_trades, load_strategy_backtests,
    load_strategy_tournament, load_paper_campaign
)
from execution_prototype.risk_governor.trust_score import calculate_trust_score
from execution_prototype.risk_governor.risk_rules import run_all_rules
from execution_prototype.risk_governor.governor import make_governor_decision
from execution_prototype.risk_governor.report_writer import write_reports

def main():
    parser = argparse.ArgumentParser(description="Phase 38 Risk Governor")
    parser.add_argument("--phase36-report", required=True, help="Path to Phase 36 report dir")
    parser.add_argument("--phase37-report", required=True, help="Path to Phase 37 report dir")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--phase33-report", help="Path to Phase 33 report dir")
    parser.add_argument("--phase34-report", help="Path to Phase 34 report dir")
    parser.add_argument("--phase35-report", help="Path to Phase 35 report dir")
    parser.add_argument("--strict", action="store_true", help="Fail if missing data")
    parser.add_argument("--dry-run", action="store_true", help="Do not write outputs")
    
    args = parser.parse_args()
    
    p36 = Path(args.phase36_report)
    p37 = Path(args.phase37_report)
    p33 = Path(args.phase33_report) if args.phase33_report else None
    p34 = Path(args.phase34_report) if args.phase34_report else None
    p35 = Path(args.phase35_report) if args.phase35_report else None
    out_dir = Path(args.output_dir)
    
    if args.strict and (not p36.exists() or not p37.exists()):
        print("Error: Required input directories missing in strict mode.")
        sys.exit(1)
        
    candidates = load_meme_candidates(p34) if p34 else []
    paper_trades = load_paper_trades(p36) if p36 else []
    paper_decisions = load_paper_decisions(p36) if p36 else []
    paper_review = load_paper_review(p35) if p35 else None
    early_warnings = load_early_warnings(p33) if p33 else []
    strategy_backtests = load_strategy_backtests(p37) if p37 else []
    strategy_tournament = load_strategy_tournament(p37) if p37 else None
    campaign = load_paper_campaign(p36) if p36 else None
    
    trust_score = calculate_trust_score(
        candidates, paper_trades, paper_decisions, paper_review,
        early_warnings, strategy_backtests, strategy_tournament
    )
    
    rules = run_all_rules(candidates, paper_decisions, paper_review, early_warnings, strategy_tournament)
    
    decision = make_governor_decision(trust_score, rules, campaign.get("campaign_id") if campaign else None)
    
    if not args.dry_run:
        write_reports(out_dir, trust_score, rules, decision)
        print(f"Risk Governor completed. Output saved to {out_dir}")
        
    sys.exit(0)

if __name__ == "__main__":
    main()
