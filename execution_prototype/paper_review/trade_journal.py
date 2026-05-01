import hashlib
from typing import List, Dict, Any, Optional
from execution_prototype.paper_review.models import PaperTradeHistory

def _generate_trade_id(campaign_id: str, candidate_id: str, entry_decision_id: str) -> str:
    basis = f"{campaign_id}|{candidate_id}|{entry_decision_id}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def _evaluate_outcome(
    entry_price: Optional[float], 
    exit_price: Optional[float]
) -> tuple[str, Optional[float], Optional[float], List[str]]:
    mistakes = []
    if entry_price is None or exit_price is None:
        mistakes.append("UNKNOWN_PRICE_OUTCOME")
        return "unknown", None, None, mistakes
        
    pnl_xrp = exit_price - entry_price
    # Assume long for paper trades here (or we could determine based on buy/sell)
    # The prompt says: Win: paper_pnl_pct > 0, Loss: paper_pnl_pct < 0, Breakeven == 0
    if entry_price == 0:
        pnl_pct = 0.0
    else:
        pnl_pct = (pnl_xrp / entry_price) * 100.0
        
    if pnl_pct > 0:
        outcome = "win"
    elif pnl_pct < 0:
        outcome = "loss"
    else:
        outcome = "breakeven"
        
    return outcome, pnl_xrp, pnl_pct, mistakes

def _generate_tags(trade_data: Dict[str, Any], outcome: str) -> tuple[List[str], List[str], List[str]]:
    mistake_tags = []
    success_tags = []
    improvements = []
    
    meta_present = trade_data.get("metadata_present_at_entry", False)
    validated = trade_data.get("validated_ledger_evidence", False)
    amm_present = trade_data.get("amm_present", False)
    signal_types = set(trade_data.get("source_signal_types", []))
    risk_flags = trade_data.get("risk_flags_at_entry", [])
    score = trade_data.get("entry_score", 0)
    liquidity_strength = trade_data.get("liquidity_signal_strength", "none")
    
    if not meta_present:
        mistake_tags.append("WEAK_METADATA_ENTRY")
        improvements.append("Review stricter metadata requirements manually.")
    else:
        success_tags.append("METADATA_BACKED_DECISION")
        
    if not validated:
        mistake_tags.append("NO_VALIDATED_LEDGER_ENTRY")
    else:
        success_tags.append("VALIDATED_LEDGER_BACKED")
        
    if "offer_activity_low_confidence" in signal_types and "trustline_created" not in signal_types and not amm_present:
        mistake_tags.append("OFFER_ONLY_ENTRY")
        improvements.append("Review whether OfferCreate-only setups should remain low confidence.")
        
    if not amm_present:
        mistake_tags.append("NO_AMM_LIQUIDITY")
    else:
        success_tags.append("AMM_BACKED_ENTRY")
        
    if liquidity_strength in ["none", "weak"] and not amm_present:
        mistake_tags.append("LOW_LIQUIDITY_ENTRY")
        improvements.append("Review liquidity thresholds manually.")
        
    if score >= 75 and outcome == "loss":
        mistake_tags.append("OVERCONFIDENT_SCORE")
        
    if "POSSIBLE_SPAM_ISSUER" in risk_flags or "ISSUER_REUSE_PATTERN" in risk_flags:
        mistake_tags.append("POSSIBLE_RUG_RISK_IGNORED")
        improvements.append("Review issuer-risk filtering manually.")
        
    if "trustline_created" in signal_types:
        success_tags.append("TRUSTLINE_BACKED_ENTRY")
        
    if "FIRSTLEDGER_UNAVAILABLE" in risk_flags and "offer_activity_low_confidence" in signal_types:
        mistake_tags.append("FIRSTLEDGER_SIGNAL_TOO_WEAK")
        
    if outcome == "win":
        success_tags.append("PROFIT_TARGET_HIT")
        
    return list(set(mistake_tags)), list(set(success_tags)), list(set(improvements))

def create_paper_trade(
    campaign_id: str,
    candidate_id: str,
    issuer: str,
    currency_code: str,
    entry_decision_id: str,
    entry_time: str,
    entry_score: int,
    entry_score_band: str,
    entry_reason: str,
    risk_flags_at_entry: List[str],
    evidence_event_ids: List[str],
    source_signal_types: List[str],
    metadata_present_at_entry: bool,
    validated_ledger_evidence: bool,
    amm_present: bool,
    liquidity_signal_strength: str,
    paper_size_xrp: float,
    entry_price_paper: Optional[float] = None,
    exit_decision_id: Optional[str] = None,
    exit_time: Optional[str] = None,
    exit_score: Optional[int] = None,
    exit_score_band: Optional[str] = None,
    exit_reason: Optional[str] = None,
    risk_flags_at_exit: Optional[List[str]] = None,
    exit_price_paper: Optional[float] = None
) -> PaperTradeHistory:
    
    outcome, pnl_xrp, pnl_pct, explicit_mistakes = _evaluate_outcome(entry_price_paper, exit_price_paper)
    
    trade_data = {
        "metadata_present_at_entry": metadata_present_at_entry,
        "validated_ledger_evidence": validated_ledger_evidence,
        "amm_present": amm_present,
        "source_signal_types": source_signal_types,
        "risk_flags_at_entry": risk_flags_at_entry,
        "entry_score": entry_score,
        "liquidity_signal_strength": liquidity_signal_strength
    }
    
    mistakes, successes, improvements = _generate_tags(trade_data, outcome)
    mistakes.extend(explicit_mistakes)
    
    # Simple additional logic
    if exit_reason and "DECAY" in exit_reason.upper():
        successes.append("EXITED_ON_CONFIDENCE_DECAY")
        
    if pnl_pct is not None and pnl_pct < -20.0:
        mistakes.append("BAD_RISK_REWARD")
        
    trade_id = _generate_trade_id(campaign_id, candidate_id, entry_decision_id)
    
    return PaperTradeHistory(
        trade_id=trade_id,
        campaign_id=campaign_id,
        candidate_id=candidate_id,
        issuer=issuer,
        currency_code=currency_code,
        entry_decision_id=entry_decision_id,
        exit_decision_id=exit_decision_id,
        entry_time=entry_time,
        exit_time=exit_time,
        entry_score=entry_score,
        exit_score=exit_score,
        entry_score_band=entry_score_band,
        exit_score_band=exit_score_band,
        entry_reason=entry_reason,
        exit_reason=exit_reason,
        risk_flags_at_entry=risk_flags_at_entry,
        risk_flags_at_exit=risk_flags_at_exit or [],
        evidence_event_ids=evidence_event_ids,
        source_signal_types=source_signal_types,
        metadata_present_at_entry=metadata_present_at_entry,
        validated_ledger_evidence=validated_ledger_evidence,
        amm_present=amm_present,
        liquidity_signal_strength=liquidity_signal_strength,
        paper_size_xrp=paper_size_xrp,
        entry_price_paper=entry_price_paper,
        exit_price_paper=exit_price_paper,
        paper_pnl_xrp=pnl_xrp,
        paper_pnl_pct=pnl_pct,
        outcome=outcome,
        mistake_tags=list(set(mistakes)),
        success_tags=list(set(successes)),
        improvement_notes=improvements
    )
