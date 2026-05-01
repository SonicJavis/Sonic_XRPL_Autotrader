import argparse
import sys
from datetime import datetime, timezone
from execution_prototype.drift_intelligence.loaders import load_historical_runs
from execution_prototype.drift_intelligence.trend_analyzer import analyze_trends
from execution_prototype.drift_intelligence.confidence_engine import calculate_confidence_decay
from execution_prototype.drift_intelligence.replay_validator import validate_replay
from execution_prototype.drift_intelligence.early_warning import detect_early_warnings
from execution_prototype.drift_intelligence.models import DriftSummary
from execution_prototype.drift_intelligence.report_writer import write_reports

SCHEMA_VERSION = "1.0.0"

def main():
    parser = argparse.ArgumentParser(description="Phase 33 Drift Intelligence")
    parser.add_argument("--phase30-root", required=True, help="Path to Phase 30 reports root")
    parser.add_argument("--phase31-root", required=True, help="Path to Phase 31 reports root")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    try:
        runs = load_historical_runs(args.phase30_root, args.phase31_root)
    except Exception as e:
        print(f"Error loading historical runs: {e}")
        sys.exit(1)
        
    if not runs:
        print("No historical runs found. Drift intelligence requires historical data.")
        sys.exit(0)
        
    trends = analyze_trends(runs)
    decays = calculate_confidence_decay(runs)
    replays = validate_replay(runs)
    warnings = detect_early_warnings(trends, decays)
    
    system_degrading = any(w.severity in ["high", "critical"] for w in warnings)
    
    summary = DriftSummary(
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_runs_analyzed=len(runs),
        start_run_hash=runs[0]["run_id"] if runs else "N/A",
        end_run_hash=runs[-1]["run_id"] if runs else "N/A",
        active_warnings_count=len(warnings),
        system_degrading=system_degrading,
        safety_statement="This report is an analytical intelligence tool. It contains no execution logic and implements no auto-calibration."
    )
    
    write_reports(args.output_dir, trends, decays, replays, warnings, summary)
    
    print(f"Drift Intelligence completed. Analyzed {len(runs)} runs.")
    print(f"Found {len(warnings)} early warnings.")
    if system_degrading:
        print("WARNING: System degradation detected. High/Critical warnings active.")
        
    sys.exit(0)

if __name__ == "__main__":
    main()
