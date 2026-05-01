import argparse
import sys
import json
from datetime import datetime, timezone
from execution_prototype.calibration_recommendations.loaders import load_phase30_report
from execution_prototype.calibration_recommendations.analyzer import analyze_records, SCHEMA_VERSION
from execution_prototype.calibration_recommendations.recommendation_engine import generate_recommendations
from execution_prototype.calibration_recommendations.models import CalibrationSummary
from execution_prototype.calibration_recommendations.report_writer import write_reports

def main():
    parser = argparse.ArgumentParser(description="Phase 31 Human-Guided Calibration Recommendations")
    parser.add_argument("--phase30-report", required=True, help="Path to Phase 30 report directory")
    parser.add_argument("--output-dir", required=True, help="Output directory for recommendations")
    parser.add_argument("--format", choices=["jsonl", "md", "both"], default="both", help="Output format")
    parser.add_argument("--strict", action="store_true", help="Fail strictly if records are missing")
    
    args = parser.parse_args()
    
    try:
        records, report_hash, p30_summary, p30_limitations = load_phase30_report(args.phase30_report)
    except FileNotFoundError as e:
        if args.strict:
            print(f"Error: {e}")
            sys.exit(1)
        else:
            print(f"Warning: {e}")
            records, report_hash, p30_summary, p30_limitations = [], "", {}, []
            
    observations = analyze_records(records, report_hash)
    recommendations = generate_recommendations(observations)
    
    cat_counts = {}
    sev_counts = {}
    conf_counts = {}
    
    for rec in recommendations:
        cat_counts[rec.category] = cat_counts.get(rec.category, 0) + 1
        sev_counts[rec.severity] = sev_counts.get(rec.severity, 0) + 1
        conf_counts[rec.confidence] = conf_counts.get(rec.confidence, 0) + 1
        
    summary = CalibrationSummary(
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        phase30_report_path=args.phase30_report,
        phase30_report_hash=report_hash,
        total_observations=len(observations),
        total_recommendations=len(recommendations),
        recommendation_counts_by_category=cat_counts,
        recommendation_counts_by_severity=sev_counts,
        confidence_counts=conf_counts,
        major_limitations=list(set(p30_limitations + [lim for obs in observations for lim in obs.limitations])),
        safety_statement="This report provides human-guided calibration recommendations. It is purely analytical and does not execute, modify, or auto-calibrate any trading systems."
    )
    
    out_info = write_reports(observations, recommendations, summary, args.output_dir, args.format)
    
    print("\nCALIBRATION RECOMMENDATIONS SUMMARY:")
    print(json.dumps(out_info["summary"]["recommendation_counts_by_category"], indent=2))
    print(f"Total Recommendations: {len(recommendations)}")
    print("\nFILES CREATED:")
    for f in out_info["files"]:
        print(f"- {f}")
        
    sys.exit(0)

if __name__ == "__main__":
    main()
