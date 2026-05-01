import json
from pathlib import Path
from typing import List
from datetime import datetime, timezone

from execution_prototype.drift_intelligence.models import (
    DriftTrend, ConfidenceDecay, ReplayRecord, EarlyWarning, DriftSummary
)

def write_reports(
    output_dir: str,
    trends: List[DriftTrend],
    decays: List[ConfidenceDecay],
    replays: List[ReplayRecord],
    warnings: List[EarlyWarning],
    summary: DriftSummary
):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir) / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    with open(out_path / "drift_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary.to_dict(), f, indent=2)
        
    with open(out_path / "drift_trends.jsonl", "w", encoding="utf-8") as f:
        for t in trends:
            f.write(json.dumps(t.to_dict()) + "\n")
            
    with open(out_path / "confidence_decay.jsonl", "w", encoding="utf-8") as f:
        for d in decays:
            f.write(json.dumps(d.to_dict()) + "\n")
            
    with open(out_path / "replay_validation.jsonl", "w", encoding="utf-8") as f:
        for r in replays:
            f.write(json.dumps(r.to_dict()) + "\n")
            
    with open(out_path / "early_warnings.jsonl", "w", encoding="utf-8") as f:
        for w in warnings:
            f.write(json.dumps(w.to_dict()) + "\n")
            
    _write_markdown(out_path / "drift_intelligence.md", trends, decays, replays, warnings, summary)

def _write_markdown(path: Path, trends: List[DriftTrend], decays: List[ConfidenceDecay], 
                    replays: List[ReplayRecord], warnings: List[EarlyWarning], summary: DriftSummary):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Phase 33 Drift Intelligence\n\n")
        f.write("## 1. System Health Overview\n")
        f.write(f"- **Runs Analyzed**: {summary.total_runs_analyzed}\n")
        f.write(f"- **System Degrading**: {summary.system_degrading}\n")
        f.write(f"- **Active Warnings**: {summary.active_warnings_count}\n\n")
        
        f.write("## 2. Drift Trends (normalized)\n")
        for t in trends:
            f.write(f"### {t.drift_flag}\n")
            f.write(f"- Trend: {t.trend_direction.upper()} (Slope: {t.slope_score:.3f})\n")
            f.write(f"- Confidence: {t.confidence.upper()}\n\n")
            
        f.write("## 3. Confidence Analysis\n")
        for d in decays:
            f.write(f"- **{d.metric}**: Prev={d.previous_value:.2f}, Curr={d.current_value:.2f}, Decay={d.decay_rate:.2f}\n")
            if d.metadata_dependency:
                f.write("  - *Warning*: High Metadata Dependency\n")
        f.write("\n")
        
        f.write("## 4. Replay Determinism Check\n")
        failed_replays = [r for r in replays if not r.deterministic_match]
        if failed_replays:
            f.write(f"Found {len(failed_replays)} non-deterministic replays.\n")
            for r in failed_replays[:5]:
                f.write(f"- ID {r.reconciliation_id}: {r.deviation_type} ({' '.join(r.notes)})\n")
        else:
            f.write("All historical replays proved deterministic.\n")
        f.write("\n")
        
        f.write("## 5. Early Warnings\n")
        if not warnings:
            f.write("No active early warnings.\n\n")
        for w in warnings:
            f.write(f"### {w.type.upper()} ({w.severity.upper()})\n")
            f.write(f"- **Description**: {w.description}\n")
            f.write(f"- **Evidence**: {w.evidence}\n")
            f.write(f"- **Required Action**: {w.recommended_human_action}\n")
            f.write(f"- **Prohibited**: {w.prohibited_auto_action}\n\n")
            
        f.write("## 6. Risk Assessment\n")
        f.write("Any active critical warnings imply the simulation models cannot be safely relied upon for future execution.\n\n")
        
        f.write("## 7. Limitations\n")
        f.write("This engine requires at least 3 runs to calculate drift slopes. It cannot overcome fundamental absence of XRPL metadata.\n\n")
        
        f.write("## 8. Safety Statement\n")
        f.write(f"{summary.safety_statement}\n")
