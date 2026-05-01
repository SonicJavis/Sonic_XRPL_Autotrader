import json
from pathlib import Path
from typing import Dict, Any, List

from execution_prototype.campaign_runner.models import CampaignRunState, CampaignCycleResult, CampaignDashboardData

def build_dashboard_data(
    state: CampaignRunState,
    latest_cycle: CampaignCycleResult,
    p36_dir: Path,
    p37_dir: Path,
    p38_dir: Path
) -> CampaignDashboardData:
    
    # Defaults
    paper_summary = {"balance": 0.0, "pnl": 0.0, "open": 0, "closed": 0, "unknown": 0}
    trade_journal = []
    protocol_context = []
    limitations = state.limitations.copy()
    
    # Load p36
    if p36_dir and p36_dir.exists():
        p_file = p36_dir / "paper_ledger_state.json"
        if p_file.exists():
            with open(p_file, "r") as f:
                d = json.load(f)
                paper_summary["balance"] = d.get("total_equity", 0.0)
                paper_summary["pnl"] = d.get("total_realized_pnl", 0.0)
                
        p_trades = p36_dir / "paper_trade_history.jsonl"
        if p_trades.exists():
            with open(p_trades, "r") as f:
                for line in f:
                    if line.strip():
                        trade_journal.append(json.loads(line))
        paper_summary["closed"] = len(trade_journal)
        
    strat_sum = {"best_strategy": "Unknown", "unknown_rate": 0.0, "metadata_backed_rate": 0.0, "ranked": []}
    if p37_dir and p37_dir.exists():
        s_file = p37_dir / "strategy_tournament_results.json"
        if s_file.exists():
            with open(s_file, "r") as f:
                d = json.load(f)
                ranked = d.get("ranked_strategies", [])
                strat_sum["ranked"] = ranked
                if ranked:
                    best = ranked[0]
                    strat_sum["best_strategy"] = best.get("strategy_id", "Unknown")
                    strat_sum["unknown_rate"] = best.get("unknown_outcome_rate", 0.0)
                    strat_sum["metadata_backed_rate"] = best.get("metadata_backed_success_rate", 0.0)
                    
    risk_sum = {"decision": "insufficient_data", "triggered": [], "critical": []}
    if p38_dir and p38_dir.exists():
        r_file = p38_dir / "risk_rule_results.jsonl"
        if r_file.exists():
            with open(r_file, "r") as f:
                for line in f:
                    if line.strip():
                        r_data = json.loads(line)
                        if not r_data.get("passed", True):
                            risk_sum["triggered"].append(r_data.get("rule_name"))
                            if r_data.get("severity") == "critical":
                                risk_sum["critical"].append(r_data.get("rule_name"))
                                
    # Hardcoded Protocol contexts
    protocol_context = [
        "AMM context: Enabled",
        "Clawback / AMMClawback: Final / Draft",
        "MPT / Permissioned DEX: Draft",
        "Batch / fixBatchInnerSigs: Disabled / Unsupported",
        "Do not assume draft/unconfirmed features are live"
    ]
    
    limitations.extend([
        "Offline fixture simulation only.",
        "Missing price data creates unknown PnL."
    ])

    # Phase 40 Optional enrichment
    p40_path = p38_dir.parent / "phase40"
    p40_summary = None
    if p40_path.exists():
        subs = sorted([d for d in p40_path.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime)
        if subs:
            summ_file = subs[-1] / "market_fixture_summary.json"
            if summ_file.exists():
                with open(summ_file, "r") as f:
                    p40_summary = json.load(f)

    return CampaignDashboardData(
        campaign=state.to_dict(),
        latest_cycle=latest_cycle.to_dict(),
        trust_score=state.trust_score,
        governor_decision=state.governor_decision or "insufficient_data",
        paper_summary=paper_summary,
        strategy_summary=strat_sum,
        risk_summary=risk_sum,
        trade_journal_preview=trade_journal[-5:],
        protocol_context=protocol_context,
        limitations=list(set(limitations)),
        safety_statement="PAPER ONLY. NO WALLET. NO SIGNING. NO SUBMISSION. NO XAMAN PAYLOAD CREATION. LIVE TRADING FORBIDDEN.",
        market_fixture_summary=p40_summary
    )
