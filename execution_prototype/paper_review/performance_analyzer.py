import hashlib
from typing import List, Dict, Any
from execution_prototype.paper_review.models import PaperTradeHistory, PerformanceReview

def _generate_review_id(campaign_id: str, trades: List[PaperTradeHistory]) -> str:
    trade_ids = sorted(t.trade_id for t in trades)
    basis = f"{campaign_id}|{'|'.join(trade_ids)}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def analyze_performance(campaign_id: str, trades: List[PaperTradeHistory]) -> PerformanceReview:
    total_trades = len(trades)
    
    if total_trades == 0:
        return PerformanceReview(
            review_id=hashlib.sha256(campaign_id.encode("utf-8")).hexdigest()[:16],
            campaign_id=campaign_id,
            total_trades=0,
            wins=0, losses=0, breakevens=0, unknown_outcomes=0,
            win_rate=None, avg_win_pct=None, avg_loss_pct=None,
            best_trade_id=None, worst_trade_id=None,
            best_setup_tags=[], worst_setup_tags=[],
            repeated_mistakes=[], strongest_setups=[], weakest_setups=[],
            what_worked=[], what_failed=[], improve_next_time=[]
        )
        
    wins = [t for t in trades if t.outcome == "win"]
    losses = [t for t in trades if t.outcome == "loss"]
    breakevens = [t for t in trades if t.outcome == "breakeven"]
    unknowns = [t for t in trades if t.outcome == "unknown"]
    
    avg_win = sum(t.paper_pnl_pct for t in wins if t.paper_pnl_pct is not None) / len(wins) if wins else None
    avg_loss = sum(t.paper_pnl_pct for t in losses if t.paper_pnl_pct is not None) / len(losses) if losses else None
    win_rate = (len(wins) / total_trades) * 100.0 if total_trades > 0 else 0.0
    
    best_trade = max((t for t in wins if t.paper_pnl_pct is not None), key=lambda x: x.paper_pnl_pct, default=None)
    worst_trade = min((t for t in losses if t.paper_pnl_pct is not None), key=lambda x: x.paper_pnl_pct, default=None)
    
    # Aggregating tags
    all_mistakes = {}
    all_successes = {}
    all_improvements = set()
    
    for t in trades:
        for m in t.mistake_tags:
            all_mistakes[m] = all_mistakes.get(m, 0) + 1
        for s in t.success_tags:
            all_successes[s] = all_successes.get(s, 0) + 1
        for imp in t.improvement_notes:
            all_improvements.add(imp)
            
    repeated_mistakes = [m for m, count in all_mistakes.items() if count > 1]
    
    best_setup_tags = best_trade.success_tags if best_trade else []
    worst_setup_tags = worst_trade.mistake_tags if worst_trade else []
    
    strongest_setups = [s for s, c in sorted(all_successes.items(), key=lambda x: x[1], reverse=True)[:3]]
    weakest_setups = [m for m, c in sorted(all_mistakes.items(), key=lambda x: x[1], reverse=True)[:3]]
    
    what_worked = [f"{s} appeared in multiple successful trades." for s in strongest_setups]
    what_failed = [f"{m} consistently caused losses or degraded outcomes." for m in weakest_setups]
    
    # Default improvements if none specific found
    improve_next_time = list(all_improvements)
    if not improve_next_time:
        improve_next_time.append("Improve candidate discovery evidence collection.")
        improve_next_time.append("Improve price capture before next paper campaign.")
        
    return PerformanceReview(
        review_id=_generate_review_id(campaign_id, trades),
        campaign_id=campaign_id,
        total_trades=total_trades,
        wins=len(wins),
        losses=len(losses),
        breakevens=len(breakevens),
        unknown_outcomes=len(unknowns),
        win_rate=win_rate,
        avg_win_pct=avg_win,
        avg_loss_pct=avg_loss,
        best_trade_id=best_trade.trade_id if best_trade else None,
        worst_trade_id=worst_trade.trade_id if worst_trade else None,
        best_setup_tags=best_setup_tags,
        worst_setup_tags=worst_setup_tags,
        repeated_mistakes=repeated_mistakes,
        strongest_setups=strongest_setups,
        weakest_setups=weakest_setups,
        what_worked=what_worked,
        what_failed=what_failed,
        improve_next_time=improve_next_time
    )
