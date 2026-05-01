import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone
from execution_prototype.risk_governor.models import OperatorTrustScore, RiskRuleResult, RiskGovernorDecision

def write_reports(
    output_dir: Path,
    trust_score: OperatorTrustScore,
    rule_results: List[RiskRuleResult],
    decision: RiskGovernorDecision
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    with open(out_path / "operator_trust_score.json", "w", encoding="utf-8") as f:
        json.dump(trust_score.to_dict(), f, indent=2)
        
    with open(out_path / "risk_rule_results.jsonl", "w", encoding="utf-8") as f:
        for r in rule_results:
            f.write(json.dumps(r.to_dict()) + "\n")
            
    with open(out_path / "risk_governor_decision.json", "w", encoding="utf-8") as f:
        json.dump(decision.to_dict(), f, indent=2)
        
    _write_markdown(out_path / "risk_governor_report.md", trust_score, rule_results, decision)

def _write_markdown(path: Path, trust_score: OperatorTrustScore, rule_results: List[RiskRuleResult], decision: RiskGovernorDecision):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Risk Governor & Operator Trust Report\n\n")
        
        f.write("## 1. Research Sources Checked\n")
        f.write("- XRPL Known Amendments (AMM, Clawback, MPT, DID enabled. Batch/fixBatchInnerSigs disabled/unsupported in 3.1.1+).\n")
        f.write("- `rippled` Release Notes (3.1.2 security patch, 3.1.1 Batch disable).\n")
        f.write("- XLS Standards (XLS-39 Final, XLS-73 Draft, XLS-82 Draft).\n\n")
        
        f.write("## 2. Risk Governor Summary\n")
        f.write(f"- Decision ID: `{decision.decision_id}`\n")
        f.write(f"- Campaign ID: `{decision.campaign_id or 'None'}`\n\n")
        
        f.write("## 3. Operator Trust Score\n")
        f.write(f"- Overall Score: **{trust_score.overall_score}**\n")
        f.write(f"- Confidence Band: **{trust_score.confidence_band.upper()}**\n\n")
        
        f.write("## 4. Component Scores\n")
        f.write(f"- Data Quality: {trust_score.data_quality_score}\n")
        f.write(f"- Strategy Quality: {trust_score.strategy_quality_score}\n")
        f.write(f"- Drift Stability: {trust_score.drift_stability_score}\n")
        f.write(f"- Paper Performance: {trust_score.paper_performance_score}\n")
        f.write(f"- Metadata Completeness: {trust_score.metadata_completeness_score}\n")
        f.write(f"- Validation Integrity: {trust_score.validation_integrity_score}\n")
        f.write(f"- Protocol Risk: {trust_score.protocol_risk_score}\n\n")
        
        f.write("## 5. Rule Results\n")
        for r in rule_results:
            status = "PASS" if r.passed else "FAIL"
            f.write(f"- [{status}] **{r.rule_name}** (Severity: {r.severity})\n")
        f.write("\n")
        
        f.write("## 6. Critical Failures\n")
        crit = [r for r in rule_results if not r.passed and r.severity == "critical"]
        for r in crit:
            f.write(f"- **{r.rule_name}**: {', '.join(r.evidence)}\n")
        if not crit:
            f.write("- None detected.\n")
        f.write("\n")
        
        f.write("## 7. Protocol Feature Risks\n")
        if trust_score.protocol_risk_score < 100:
            f.write("- Protocol feature risks detected (e.g. Clawback, AMMClawback). See constraints.\n")
        else:
            f.write("- No advanced protocol feature risks detected in candidates.\n")
        f.write("\n")
        
        f.write("## 8. Paper Trading Decision\n")
        f.write(f"- **{decision.decision.upper()}**\n\n")
        
        f.write("## 9. Required Human Actions\n")
        f.write(f"- {decision.required_human_action}\n\n")
        
        f.write("## 10. Why Live Trading Is Still Forbidden\n")
        f.write("- Live readiness strictly failed by policy (`RULE_LIVE_1`).\n")
        f.write("- Real fund movement remains outside the execution boundary.\n\n")
        
        f.write("## 11. Limitations\n")
        for lim in trust_score.limitations:
            f.write(f"- {lim}\n")
        f.write("\n")
        
        f.write("## 12. Next Phase Recommendation\n")
        f.write("- The system has reached a stable paper architecture. Recommend shifting to frontend visualization to allow human oversight of the generated reports.\n")
