import argparse
import sys
import json
from pathlib import Path
from execution_prototype.paper_review.trade_journal import create_paper_trade
from execution_prototype.paper_review.performance_analyzer import analyze_performance
from execution_prototype.paper_review.report_writer import write_reports

def main():
    parser = argparse.ArgumentParser(description="Phase 35 Paper Review Layer")
    parser.add_argument("--input", required=True, help="Path to input paper trade events (JSONL)")
    parser.add_argument("--campaign", required=True, help="Campaign ID")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {args.input} does not exist.")
        sys.exit(1)
        
    trades = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            # Adapt input dictionary to create_paper_trade kwargs
            t = create_paper_trade(**data)
            trades.append(t)
            
    review = analyze_performance(args.campaign, trades)
    write_reports(args.output_dir, trades, review)
    
    print(f"Paper Review complete. Processed {len(trades)} trades.")
    sys.exit(0)

if __name__ == "__main__":
    main()
