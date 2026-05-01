import json
from pathlib import Path
from typing import List
from datetime import datetime, timezone

from execution_prototype.paper_review.models import PaperTradeHistory, PerformanceReview

def write_reports(
    output_dir: str,
    trades: List[PaperTradeHistory],
    review: PerformanceReview
):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(output_dir) / timestamp
    out_path.mkdir(parents=True, exist_ok=True)
    
    with open(out_path / "paper_performance_review.json", "w", encoding="utf-8") as f:
        json.dump(review.to_dict(), f, indent=2)
        
    with open(out_path / "paper_trade_history.jsonl", "w", encoding="utf-8") as f:
        for t in trades:
            f.write(json.dumps(t.to_dict()) + "\n")
            
    _write_markdown(out_path / "paper_lessons_learned.md", trades, review)

def _write_markdown(path: Path, trades: List[PaperTradeHistory], review: PerformanceReview):
    with open(path, "w", encoding="utf-8") as f:
        f.write("# 7-Day Paper Trading Lessons\n\n")
        
        f.write("## 1. Campaign Overview\n")
        f.write(f"- **Campaign ID**: {review.campaign_id}\n")
        f.write(f"- **Total Trades**: {review.total_trades}\n")
        wr_str = f"{review.win_rate:.2f}%" if review.win_rate is not None else "N/A"
        f.write(f"- **Win Rate**: {wr_str}\n")
        f.write(f"- **Wins/Losses/Breakevens**: {review.wins}/{review.losses}/{review.breakevens}\n")
        f.write(f"- **Unknown Outcomes**: {review.unknown_outcomes}\n\n")
        
        f.write("## 2. Trading History\n")
        for t in trades:
            f.write(f"### {t.currency_code} ({t.issuer})\n")
            f.write(f"- Outcome: **{t.outcome.upper()}** (PnL: {t.paper_pnl_pct:.2f}%)\n" if t.paper_pnl_pct is not None else f"- Outcome: **{t.outcome.upper()}**\n")
            f.write(f"- Success Tags: {', '.join(t.success_tags)}\n")
            f.write(f"- Mistake Tags: {', '.join(t.mistake_tags)}\n\n")
            
        f.write("## 3. Best Paper Trades\n")
        f.write(f"Best Trade ID: {review.best_trade_id}\n")
        f.write(f"Best Setup Tags: {', '.join(review.best_setup_tags)}\n\n")
        
        f.write("## 4. Worst Paper Trades\n")
        f.write(f"Worst Trade ID: {review.worst_trade_id}\n")
        f.write(f"Worst Setup Tags: {', '.join(review.worst_setup_tags)}\n\n")
        
        f.write("## 5. What Worked\n")
        for item in review.what_worked:
            f.write(f"- {item}\n")
        if not review.what_worked:
            f.write("- No clear positive patterns emerged.\n")
        f.write("\n")
            
        f.write("## 6. What Failed\n")
        for item in review.what_failed:
            f.write(f"- {item}\n")
        if not review.what_failed:
            f.write("- No clear negative patterns emerged.\n")
        f.write("\n")
            
        f.write("## 7. Repeated Mistakes\n")
        for item in review.repeated_mistakes:
            f.write(f"- {item}\n")
        if not review.repeated_mistakes:
            f.write("- No repeated mistakes detected.\n")
        f.write("\n")
            
        f.write("## 8. Strongest Setups\n")
        for item in review.strongest_setups:
            f.write(f"- {item}\n")
        f.write("\n")
            
        f.write("## 9. Weakest Setups\n")
        for item in review.weakest_setups:
            f.write(f"- {item}\n")
        f.write("\n")
            
        f.write("## 10. Improvements for Next Paper Campaign\n")
        for item in review.improve_next_time:
            f.write(f"- {item}\n")
        f.write("\n")
            
        f.write("## 11. Human Review Checklist\n")
        f.write("- [ ] Review stricter metadata requirements manually\n")
        f.write("- [ ] Review liquidity thresholds manually\n")
        f.write("- [ ] Review issuer-risk filtering manually\n")
        f.write("- [ ] Review whether OfferCreate-only setups should remain low confidence\n\n")
        
        f.write("## 12. Prohibited Auto-Actions\n")
        f.write(f"{review.prohibited_auto_action}\n")
        f.write("- Auto-change thresholds\n")
        f.write("- Auto-adjust strategy\n")
        f.write("- Auto-increase size\n")
        f.write("- Approve live trading\n")
        f.write("- Convert paper win into live permission\n")
        f.write("- Mutate model weights\n")
