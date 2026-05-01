import json
from pathlib import Path
from execution_prototype.campaign_runner.models import CampaignRunState, CampaignCycleResult, CampaignDashboardData

def write_outputs(
    output_dir: Path,
    state: CampaignRunState,
    cycle: CampaignCycleResult,
    dashboard: CampaignDashboardData
) -> None:
    
    camp_dir = output_dir / state.campaign_id
    camp_dir.mkdir(parents=True, exist_ok=True)
    
    with open(camp_dir / "campaign_state.json", "w", encoding="utf-8") as f:
        json.dump(state.to_dict(), f, indent=2)
        
    with open(camp_dir / "campaign_cycles.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(cycle.to_dict()) + "\n")
        
    with open(camp_dir / "campaign_dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(dashboard.to_dict(), f, indent=2)
        
    _write_markdown(camp_dir / "campaign_report.md", state, cycle, dashboard)

def _write_markdown(path: Path, state: CampaignRunState, cycle: CampaignCycleResult, dash: CampaignDashboardData):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# 7-Day Paper Campaign Report\n\n")
        
        f.write("## 1. Research Sources Checked\n")
        f.write("- XRPL Known Amendments, rippled 3.1.2 release notes, XLS standards.\n")
        f.write("- Batch is disabled. Hooks/Xahau is separate.\n\n")
        
        f.write("## 2. Campaign Summary\n")
        f.write(f"- ID: `{state.campaign_id}`\n")
        f.write(f"- Name: `{state.campaign_name}`\n")
        f.write(f"- Status: **{state.status.upper()}**\n")
        f.write(f"- Current Cycle: {state.current_cycle} / {state.max_cycles}\n\n")
        
        f.write("## 3. Cycle Timeline\n")
        f.write(f"- Latest run: {cycle.cycle_time}\n\n")
        
        f.write("## 4. Paper Trading Performance\n")
        f.write(f"- Balance: {dash.paper_summary['balance']}\n")
        f.write(f"- PnL: {dash.paper_summary['pnl']}\n\n")
        
        f.write("## 5. Strategy Performance\n")
        f.write(f"- Best: {dash.strategy_summary['best_strategy']}\n\n")
        
        f.write("## 6. Risk Governor History\n")
        f.write(f"- Governor Decision: **{state.governor_decision}**\n")
        f.write(f"- Trust Score: {state.trust_score}\n\n")
        
        f.write("## 7. Protocol Context Observed\n")
        for c in dash.protocol_context:
            f.write(f"- {c}\n")
        f.write("\n")
        
        f.write("## 8. Human Review Checklist\n")
        f.write("- [ ] Verify PnL logic\n")
        f.write("- [ ] Check triggered risk rules\n\n")
        
        f.write("## 9. Why Live Trading Is Still Forbidden\n")
        f.write("- Hardcoded rule RULE_LIVE_1 explicitly fails live context.\n\n")
        
        f.write("## 10. Limitations\n")
        for lim in dash.limitations:
            f.write(f"- {lim}\n")
