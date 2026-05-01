import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone
from execution_prototype.strategy_performance.models import StrategyEvaluation, StrategyBacktestResult, StrategyTournamentResult

def write_reports(
    output_dir: Path,
    evaluations: List[StrategyEvaluation],
    backtests: List[StrategyBacktestResult],
    tournament: StrategyTournamentResult
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    with open(out_path / "strategy_evaluations.jsonl", "w", encoding="utf-8") as f:
        for ev in evaluations:
            f.write(json.dumps(ev.to_dict()) + "\n")
            
    with open(out_path / "strategy_backtest_results.jsonl", "w", encoding="utf-8") as f:
        for b in backtests:
            f.write(json.dumps(b.to_dict()) + "\n")
            
    with open(out_path / "strategy_tournament_results.json", "w", encoding="utf-8") as f:
        json.dump(tournament.to_dict(), f, indent=2)
        
    _write_markdown(out_path / "strategy_performance_report.md", backtests, tournament)

def _write_markdown(path: Path, backtests: List[StrategyBacktestResult], tournament: StrategyTournamentResult):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Strategy Performance Tournament Report\n\n")
        
        f.write("## 1. Research Sources Checked\n")
        f.write("- XRPL.org documentation (AMM, Clawback, MPT, DID)\n")
        f.write("- XRPL Release Notes (3.1.2) & Clio (2.7.0)\n")
        f.write("- FirstLedger API status (No reliable public WS/REST for generic fetching found)\n\n")
        
        f.write("## 2. Strategy Tournament Summary\n")
        f.write(f"- Tournament ID: `{tournament.tournament_id}`\n")
        f.write(f"- Winning Strategy: **{tournament.winner_strategy_id}**\n\n")
        
        f.write("## 3. Best Performing Strategies\n")
        for st in tournament.ranked_strategies[:3]:
            f.write(f"- **{st['strategy_id']}**: Score {st['risk_adjusted_score']}, Win Rate {st['win_rate']}%\n")
        f.write("\n")
        
        f.write("## 4. Worst Performing Strategies\n")
        for st in reversed(tournament.ranked_strategies[-3:]):
            f.write(f"- **{st['strategy_id']}**: Score {st['risk_adjusted_score']}, Loss Rate {st['loss_rate']}%\n")
        f.write("\n")
        
        f.write("## 5. Conditions Where Each Strategy Worked\n")
        for c in tournament.strongest_conditions:
            f.write(f"- {c}\n")
        f.write("\n")
        
        f.write("## 6. Conditions Where Each Strategy Failed\n")
        for c in tournament.repeated_failures:
            f.write(f"- {c}\n")
        f.write("\n")
        
        f.write("## 7. XRPL Protocol Feature Notes\n")
        for p in tournament.protocol_feature_opportunities:
            f.write(f"- {p}\n")
        f.write("\n")
        
        f.write("## 8. Unknown / Missing Data Impact\n")
        f.write("- Missing price data yields `unknown` outcome.\n")
        f.write("- Missing metadata heavily penalizes strategy confidence.\n\n")
        
        f.write("## 9. Human Review Notes\n")
        f.write("- The results require manual human inspection of the actual fixtures.\n\n")
        
        f.write("## 10. Prohibited Live Actions\n")
        f.write(f"- {tournament.prohibited_auto_action}\n\n")
        
        f.write("## 11. Next Paper Campaign Recommendations\n")
        f.write("- Validate the AMM strategies more extensively in future campaigns.\n\n")
        
        f.write("## 12. Live Trading Readiness Impact\n")
        f.write("- **Still strictly 0/100.** This tournament provides hypothetical analytics, but DOES NOT grant execution authorization.\n")
