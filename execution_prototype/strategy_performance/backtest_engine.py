from typing import Dict, Any, List, Optional
import hashlib
from execution_prototype.strategy_performance.models import StrategyEvaluation, StrategyBacktestResult
from execution_prototype.strategy_performance.strategy_runner import STRATEGY_REGISTRY, _generate_evaluation_id

def _generate_backtest_id(strategy_id: str) -> str:
    basis = f"backtest|{strategy_id}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def evaluate_strategy_on_candidates(strategy_id: str, candidates: List[Dict[str, Any]]) -> List[StrategyEvaluation]:
    evaluations = []
    func = STRATEGY_REGISTRY.get(strategy_id)
    if not func:
        return evaluations
        
    for cand in candidates:
        candidate_id = cand.get("candidate_id", "unknown")
        would_enter, reason, features = func(cand)
        
        confidence = cand.get("confidence", "low")
        if not cand.get("metadata_present", False):
            confidence = "low" # Missing metadata reduces confidence
            
        eval_id = _generate_evaluation_id(strategy_id, candidate_id)
        
        evaluation = StrategyEvaluation(
            evaluation_id=eval_id,
            strategy_id=strategy_id,
            candidate_id=candidate_id,
            would_enter=would_enter,
            would_reject=not would_enter,
            would_hold=False,
            would_exit=False,
            reason=reason,
            evidence=cand.get("source_signal_types", []),
            risk_flags=cand.get("risk_flags", []),
            confidence=confidence,
            protocol_feature_context=features,
            prohibited_live_action="Live execution strictly prohibited."
        )
        evaluations.append(evaluation)
        
    return evaluations

def backtest_strategy(strategy_id: str, evaluations: List[StrategyEvaluation], paper_trades: List[Dict[str, Any]], candidates: List[Dict[str, Any]]) -> StrategyBacktestResult:
    hypothetical_entries = sum(1 for e in evaluations if e.would_enter)
    hypothetical_rejections = sum(1 for e in evaluations if e.would_reject)
    
    # Map paper trade outcomes to our candidate IDs
    paper_outcomes = {t["candidate_id"]: t for t in paper_trades}
    
    wins = 0
    losses = 0
    breakevens = 0
    unknowns = 0
    total_entered_and_resolved = 0
    
    win_pcts = []
    loss_pcts = []
    holding_times = []
    
    rejected_winner_count = 0
    false_positive_count = 0
    
    meta_success_count = 0
    meta_count = 0
    offer_fail_count = 0
    offer_count = 0
    amm_success_count = 0
    amm_count = 0
    trustline_success_count = 0
    trustline_count = 0
    
    cand_map = {c["candidate_id"]: c for c in candidates}
    
    protocol_notes = set()
    
    for ev in evaluations:
        trade = paper_outcomes.get(ev.candidate_id)
        cand = cand_map.get(ev.candidate_id, {})
        
        # protocol features
        for f in ev.protocol_feature_context:
            protocol_notes.add(f)
            
        outcome = trade.get("outcome", "unknown") if trade else "unknown"
        pnl = trade.get("paper_pnl_pct", 0.0) if trade else 0.0
        
        has_meta = cand.get("metadata_present", False)
        has_amm = cand.get("amm_present", False)
        signals = cand.get("source_signal_types", [])
        is_offer_only = "offer_activity_low_confidence" in signals and "trustline_created" not in signals and not has_amm
        has_trustline = "trustline_created" in signals
        
        if ev.would_enter:
            if outcome == "win":
                wins += 1
                win_pcts.append(pnl)
                total_entered_and_resolved += 1
                if has_meta:
                    meta_success_count += 1
                if has_amm:
                    amm_success_count += 1
                if has_trustline:
                    trustline_success_count += 1
            elif outcome == "loss":
                losses += 1
                loss_pcts.append(pnl)
                false_positive_count += 1
                total_entered_and_resolved += 1
                if is_offer_only:
                    offer_fail_count += 1
            elif outcome == "breakeven":
                breakevens += 1
                total_entered_and_resolved += 1
            else:
                unknowns += 1
                
            if has_meta:
                meta_count += 1
            if is_offer_only:
                offer_count += 1
            if has_amm:
                amm_count += 1
            if has_trustline:
                trustline_count += 1
                
        if ev.would_reject and outcome == "win":
            rejected_winner_count += 1
            
    win_rate = (wins / total_entered_and_resolved) * 100 if total_entered_and_resolved > 0 else None
    loss_rate = (losses / total_entered_and_resolved) * 100 if total_entered_and_resolved > 0 else None
    unk_rate = (unknowns / hypothetical_entries) * 100 if hypothetical_entries > 0 else 0.0
    
    avg_win = sum(win_pcts) / len(win_pcts) if win_pcts else None
    avg_loss = sum(loss_pcts) / len(loss_pcts) if loss_pcts else None
    
    meta_succ_rate = (meta_success_count / meta_count) * 100 if meta_count > 0 else None
    offer_fail_rate = (offer_fail_count / offer_count) * 100 if offer_count > 0 else None
    amm_succ_rate = (amm_success_count / amm_count) * 100 if amm_count > 0 else None
    trustline_succ_rate = (trustline_success_count / trustline_count) * 100 if trustline_count > 0 else None
    
    # Calculate deterministic risk_adjusted_score
    score = 0.0
    if win_rate is not None:
        score += win_rate * 2.0
    if avg_win is not None:
        score += avg_win * 100.0
    if avg_loss is not None:
        score += avg_loss * 50.0  # avg_loss is usually negative
        
    if meta_succ_rate is not None:
        score += meta_succ_rate * 0.5
    if amm_succ_rate is not None:
        score += amm_succ_rate * 0.5
    if trustline_succ_rate is not None:
        score += trustline_succ_rate * 0.2
        
    score -= unk_rate * 1.5
    if offer_fail_rate is not None:
        score -= offer_fail_rate * 0.5
        
    if not any(ev.confidence == "high" for ev in evaluations):
        score -= 20.0
        
    return StrategyBacktestResult(
        result_id=_generate_backtest_id(strategy_id),
        strategy_id=strategy_id,
        total_candidates=len(candidates),
        hypothetical_entries=hypothetical_entries,
        hypothetical_rejections=hypothetical_rejections,
        paper_wins=wins,
        paper_losses=losses,
        paper_breakevens=breakevens,
        unknown_outcomes=unknowns,
        win_rate=win_rate,
        loss_rate=loss_rate,
        unknown_outcome_rate=unk_rate,
        avg_win_pct=avg_win,
        avg_loss_pct=avg_loss,
        max_drawdown_paper=min(loss_pcts) if loss_pcts else None,
        average_holding_time=None,
        rejected_winner_count=rejected_winner_count,
        false_positive_count=false_positive_count,
        metadata_backed_success_rate=meta_succ_rate,
        offer_only_failure_rate=offer_fail_rate,
        amm_backed_success_rate=amm_succ_rate,
        trustline_backed_success_rate=trustline_succ_rate,
        protocol_feature_notes=list(protocol_notes),
        risk_adjusted_score=round(score, 2),
        confidence="medium" if score > 50 else "low",
        limitations=["Paper execution only", "Relies on historical fixtures"],
        prohibited_live_action="Live execution strictly prohibited."
    )
