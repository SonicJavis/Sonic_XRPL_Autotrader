from typing import List, Dict, Any, Optional
from execution_prototype.paper_operator.models import PaperLedgerState, PaperDecision, PaperPosition
from execution_prototype.paper_operator.decision_policy import evaluate_candidate
from execution_prototype.paper_operator.portfolio import apply_decision
from execution_prototype.paper_review.trade_journal import create_paper_trade
from execution_prototype.paper_review.models import PaperTradeHistory

def execute_cycle(
    candidates: List[Dict[str, Any]], 
    drift_warnings: List[Dict[str, Any]], 
    ledger: PaperLedgerState,
    price_feed: Dict[str, float]  # candidate_id -> price
) -> tuple[PaperLedgerState, List[PaperDecision], List[PaperTradeHistory]]:
    
    decisions = []
    trade_history = []
    current_ledger = ledger
    
    processed_candidate_ids = set()
    
    # Evaluate open positions first (for exits)
    for pos_candidate_id, pos in list(current_ledger.open_positions.items()):
        processed_candidate_ids.add(pos_candidate_id)
        # find candidate data if it exists in the new report, otherwise mock from pos
        candidate_data = next((c for c in candidates if c.get("candidate_id") == pos_candidate_id), None)
        if not candidate_data:
            candidate_data = {
                "candidate_id": pos_candidate_id,
                "issuer": pos.issuer,
                "currency_code": pos.currency_code,
                "score_band": "unknown",
                "confidence": "unknown",
                "risk_flags": [],
                "metadata_present": True,
                "validated_ledger_evidence": True,
                "amm_present": True,
                "liquidity_signal_strength": "unknown",
                "source_signal_types": []
            }
            
        current_price = price_feed.get(pos_candidate_id)
        decision = evaluate_candidate(
            candidate=candidate_data,
            drift_warnings=drift_warnings,
            open_position=pos,
            current_open_positions_count=len(current_ledger.open_positions),
            max_positions=current_ledger.max_positions,
            current_price_xrp=current_price
        )
        decisions.append(decision)
        
        new_ledger, closed_pos, _ = apply_decision(current_ledger, decision, current_price)
        current_ledger = new_ledger
        
        if closed_pos:
            trade = create_paper_trade(
                campaign_id=current_ledger.campaign_id,
                candidate_id=decision.candidate_id,
                issuer=decision.issuer,
                currency_code=decision.currency_code,
                entry_decision_id=closed_pos.entry_decision_id,
                entry_time=closed_pos.entry_timestamp,
                entry_score=80, # placeholder since we don't store it in pos
                entry_score_band="unknown",
                entry_reason="unknown",
                risk_flags_at_entry=[],
                evidence_event_ids=[],
                source_signal_types=[],
                metadata_present_at_entry=True,
                validated_ledger_evidence=True,
                amm_present=True,
                liquidity_signal_strength="unknown",
                paper_size_xrp=closed_pos.size_xrp,
                entry_price_paper=closed_pos.entry_price_xrp,
                exit_decision_id=decision.decision_id,
                exit_time=decision.timestamp,
                exit_score=0,
                exit_score_band="unknown",
                exit_reason=decision.reason,
                risk_flags_at_exit=decision.risk_flags,
                exit_price_paper=current_price
            )
            trade_history.append(trade)

    # Evaluate new candidates for entry
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        if candidate_id in processed_candidate_ids:
            continue # already handled above
            
        current_price = price_feed.get(candidate_id, 0.01) # fallback price for paper
        decision = evaluate_candidate(
            candidate=candidate,
            drift_warnings=drift_warnings,
            open_position=None,
            current_open_positions_count=len(current_ledger.open_positions),
            max_positions=current_ledger.max_positions,
            current_price_xrp=current_price
        )
        decisions.append(decision)
        
        new_ledger, _, opened_pos = apply_decision(current_ledger, decision, current_price)
        current_ledger = new_ledger

    return current_ledger, decisions, trade_history
