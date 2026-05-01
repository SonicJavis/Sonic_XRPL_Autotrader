import argparse
import sys
from pathlib import Path

from execution_prototype.campaign_runner.state_store import load_campaign_state, create_initial_campaign
from execution_prototype.campaign_runner.cycle_runner import run_cycle
from execution_prototype.campaign_runner.summary_builder import build_dashboard_data
from execution_prototype.campaign_runner.report_writer import write_outputs

def main():
    parser = argparse.ArgumentParser(description="Phase 39 Campaign Runner")
    parser.add_argument("--campaign-name", help="Name of new campaign")
    parser.add_argument("--campaign-id", help="ID of existing campaign")
    parser.add_argument("--discovery-report", required=True, help="Path to Phase 34 discovery report")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--duration-days", type=int, default=7, help="Max cycles")
    parser.add_argument("--starting-balance-xrp", type=float, default=1000.0, help="Initial paper balance")
    parser.add_argument("--phase33-report", help="Path to Phase 33 report")
    parser.add_argument("--run-cycle", action="store_true", help="Run a cycle")
    parser.add_argument("--strict", action="store_true", help="Fail if missing data")
    parser.add_argument("--dry-run", action="store_true", help="Do not write outputs")
    
    args = parser.parse_args()
    
    if not args.campaign_name and not args.campaign_id:
        print("Error: Must provide --campaign-name or --campaign-id")
        sys.exit(1)
        
    out_dir = Path(args.output_dir)
    disc_dir = Path(args.discovery_report)
    p33_dir = Path(args.phase33_report) if args.phase33_report else None
    
    if args.campaign_id:
        state = load_campaign_state(out_dir, args.campaign_id)
        if not state:
            print(f"Error: Campaign {args.campaign_id} not found.")
            sys.exit(1)
    else:
        state = create_initial_campaign(args.campaign_name, args.duration_days)
        
    if state.status in ["halted", "completed"] and not args.dry_run:
        print(f"Campaign is {state.status}, cannot run cycle.")
        sys.exit(1)
        
    if args.run_cycle:
        new_state, cycle_res = run_cycle(state, disc_dir, out_dir, p33_dir, args.starting_balance_xrp)
        
        # Build dashboard
        p36_path = Path(new_state.latest_phase36_report) if new_state.latest_phase36_report else None
        p37_path = Path(new_state.latest_phase37_report) if new_state.latest_phase37_report else None
        p38_path = Path(new_state.latest_phase38_report) if new_state.latest_phase38_report else None
        
        dashboard = build_dashboard_data(new_state, cycle_res, p36_path, p37_path, p38_path)
        
        if not args.dry_run:
            write_outputs(out_dir, new_state, cycle_res, dashboard)
            print(f"Campaign cycle {new_state.current_cycle} generated at {out_dir / new_state.campaign_id}")
            
    sys.exit(0)

if __name__ == "__main__":
    main()
