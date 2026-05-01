import argparse
import sys
from pathlib import Path

from execution_prototype.strategy_performance.loaders import (
    load_discovery_candidates,
    load_paper_trades,
    load_price_fixtures
)
from execution_prototype.strategy_performance.strategy_runner import STRATEGY_REGISTRY
from execution_prototype.strategy_performance.backtest_engine import evaluate_strategy_on_candidates, backtest_strategy
from execution_prototype.strategy_performance.tournament import run_tournament
from execution_prototype.strategy_performance.report_writer import write_reports

def main():
    parser = argparse.ArgumentParser(description="Phase 37 Strategy Performance Engine")
    parser.add_argument("--paper-report", required=True, help="Path to paper trade directory")
    parser.add_argument("--discovery-report", required=True, help="Path to discovery report directory")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--phase33-report", help="Path to phase 33 report")
    parser.add_argument("--price-fixtures", help="Path to price fixtures directory")
    parser.add_argument("--strict", action="store_true", help="Fail if missing data")
    parser.add_argument("--dry-run", action="store_true", help="Do not write outputs")
    
    args = parser.parse_args()
    
    paper_dir = Path(args.paper_report)
    discovery_dir = Path(args.discovery_report)
    out_dir = Path(args.output_dir)
    fixtures_dir = Path(args.price_fixtures) if args.price_fixtures else None
    
    if not discovery_dir.exists() or not paper_dir.exists():
        print("Error: Input directories do not exist.")
        sys.exit(1)
        
    candidates = load_discovery_candidates(discovery_dir)
    paper_trades = load_paper_trades(paper_dir)
    prices = load_price_fixtures(fixtures_dir) if fixtures_dir else {}
    
    if args.strict and (not candidates or not paper_trades):
        print("Error: Strict mode enabled but required data missing.")
        sys.exit(1)
        
    all_evals = []
    backtests = []
    
    for st_name in STRATEGY_REGISTRY:
        evals = evaluate_strategy_on_candidates(st_name, candidates)
        all_evals.extend(evals)
        bt = backtest_strategy(st_name, evals, paper_trades, candidates)
        backtests.append(bt)
        
    tournament = run_tournament(backtests)
    
    if not args.dry_run:
        write_reports(out_dir, all_evals, backtests, tournament)
        print(f"Strategy performance generated at {out_dir}")
        
    sys.exit(0)

if __name__ == "__main__":
    main()
