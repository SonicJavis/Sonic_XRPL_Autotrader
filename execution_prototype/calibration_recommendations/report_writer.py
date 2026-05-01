import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
from execution_prototype.calibration_recommendations.models import CalibrationObservation, CalibrationRecommendation, CalibrationSummary

def write_reports(
    observations: List[CalibrationObservation],
    recommendations: List[CalibrationRecommendation],
    summary: CalibrationSummary,
    output_dir: str,
    format: str = "both"
) -> Dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir) / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    obs_path = out_path / "calibration_observations.jsonl"
    recs_path = out_path / "calibration_recommendations.jsonl"
    summary_path = out_path / "calibration_summary.json"
    md_path = out_path / "calibration_recommendations.md"
    
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary.to_dict(), f, indent=2)
        
    if format in ["jsonl", "both"]:
        with open(obs_path, "a", encoding="utf-8") as f:
            for obs in observations:
                f.write(json.dumps(obs.to_dict()) + "\n")
                
        with open(recs_path, "a", encoding="utf-8") as f:
            for rec in recommendations:
                f.write(json.dumps(rec.to_dict()) + "\n")
                
    if format in ["md", "both"]:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Phase 31 Human-Guided Calibration Recommendations\n\n")
            f.write("## 1. Safety Statement\n")
            f.write(f"{summary.safety_statement}\n\n")
            
            f.write("## 2. Source Phase 30 Report\n")
            f.write(f"- **Path**: `{summary.phase30_report_path}`\n")
            f.write(f"- **Hash**: `{summary.phase30_report_hash}`\n\n")
            
            f.write("## 3. Summary\n")
            f.write(f"- Total Observations: {summary.total_observations}\n")
            f.write(f"- Total Recommendations: {summary.total_recommendations}\n\n")
            
            f.write("## 4. Recommendations\n")
            if not recommendations:
                f.write("No recommendations generated.\n\n")
            else:
                for rec in recommendations:
                    f.write(f"### {rec.title} ({rec.severity.upper()})\n")
                    f.write(f"- **Category**: {rec.category}\n")
                    f.write(f"- **Confidence**: {rec.confidence.upper()}\n")
                    f.write(f"- **Recommendation**: {rec.recommendation_text}\n")
                    f.write(f"- **Required Human Action**: {rec.required_human_action}\n")
                    f.write(f"- **Prohibited Auto Action**: {rec.prohibited_auto_action}\n")
                    f.write(f"- **Evidence Records**: {len(rec.evidence_record_ids)}\n\n")
                    
            f.write("## 5. Observations by Drift Flag\n")
            for obs in observations:
                f.write(f"### {obs.drift_flag}\n")
                f.write(f"- **Count**: {obs.count} ({obs.metadata_backed_count} metadata backed)\n")
                f.write(f"- **Confidence**: {obs.confidence.upper()}\n")
                f.write(f"- **Summary**: {obs.evidence_summary}\n\n")
                
            f.write("## 6. Confidence Explanation\n")
            f.write("Confidence is determined strictly by the presence of validated XRPL metadata and sufficient sample sizes. High confidence requires >=10 metadata-backed occurrences. Missing metadata always caps confidence at Low or Medium.\n\n")
            
            f.write("## 7. Limitations\n")
            for lim in summary.major_limitations:
                f.write(f"- {lim}\n")
            if not summary.major_limitations:
                f.write("- None explicitly noted.\n")
            f.write("\n")
                
            f.write("## 8. Prohibited Actions\n")
            f.write("- No auto-calibration\n")
            f.write("- No parameter mutation\n")
            f.write("- No automated trading logic updates\n")
            f.write("- No guessing or inferring missing outcome data\n")
            
    return {
        "summary": summary.to_dict(),
        "files": [str(p) for p in [summary_path, obs_path, recs_path, md_path] if p.exists()]
    }
