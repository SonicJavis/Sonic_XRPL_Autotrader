import json
from pathlib import Path
from typing import List
from datetime import datetime, timezone

from execution_prototype.discovery.models import RawDiscoveryEvent, MemeCandidate, DiscoverySummary

def write_reports(
    output_dir: str,
    events: List[RawDiscoveryEvent],
    candidates: List[MemeCandidate],
    summary: DiscoverySummary
):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir) / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    with open(out_path / "discovery_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary.to_dict(), f, indent=2)
        
    with open(out_path / "raw_discovery_events.jsonl", "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e.to_dict()) + "\n")
            
    with open(out_path / "meme_candidates.jsonl", "w", encoding="utf-8") as f:
        for c in candidates:
            f.write(json.dumps(c.to_dict()) + "\n")
            
    # Write scores explicitly (could be just part of candidates but we'll output a stripped version)
    with open(out_path / "discovery_scores.jsonl", "w", encoding="utf-8") as f:
        for c in candidates:
            score_data = {
                "candidate_id": c.candidate_id,
                "score": c.score,
                "score_band": c.score_band,
                "confidence": c.confidence
            }
            f.write(json.dumps(score_data) + "\n")
            
    _write_markdown(out_path / "discovery_report.md", candidates, summary)

def _write_markdown(path: Path, candidates: List[MemeCandidate], summary: DiscoverySummary):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Phase 34 XRPL Meme Discovery\n\n")
        f.write("## Overview\n")
        f.write(f"- **Events Processed**: {summary.total_events_processed}\n")
        f.write(f"- **Candidates Found**: {summary.total_candidates_found}\n\n")
        
        f.write("## Bands\n")
        for band, count in summary.candidates_by_band.items():
            f.write(f"- **{band.upper()}**: {count}\n")
        f.write("\n")
        
        f.write("## High Attention Candidates\n")
        high_attention = [c for c in candidates if c.score_band == "high_attention"]
        if not high_attention:
            f.write("No high attention candidates.\n\n")
        for c in high_attention:
            f.write(f"### Token: {c.currency_code} (Issuer: {c.issuer})\n")
            f.write(f"- **Score**: {c.score}\n")
            f.write(f"- **Confidence**: {c.confidence.upper()}\n")
            f.write(f"- **First Ledger**: {c.first_seen_ledger}\n")
            f.write(f"- **Risks**: {', '.join(c.risk_flags) if c.risk_flags else 'None'}\n")
            f.write(f"- *Action*: Human review required. {c.prohibited_auto_action}\n\n")
            
        f.write("## Review Candidates\n")
        review = [c for c in candidates if c.score_band == "review"]
        if not review:
            f.write("No review candidates.\n\n")
        for c in review:
            f.write(f"- **{c.currency_code}** ({c.issuer}): Score {c.score}, Confidence {c.confidence.upper()}\n")
        f.write("\n")
            
        f.write("## Limitations & Safety\n")
        f.write(f"{summary.safety_statement}\n")
