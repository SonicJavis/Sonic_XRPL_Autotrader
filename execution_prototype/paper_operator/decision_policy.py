import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from execution_prototype.paper_operator.models import PaperDecision, PaperPosition

def _generate_decision_id(candidate_id: str, timestamp: str, action: str) -> str:
    basis = f"{candidate_id}|{timestamp}|{action}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def evaluate_candidate(
    candidate: Dict[str, Any], 
    drift_warnings: List[Dict[str, Any]], 
    open_position: Optional[PaperPosition],
    current_open_positions_count: int,
    max_positions: int,
    current_price_xrp: Optional[float]
) -> PaperDecision:
    
    timestamp = datetime.now(timezone.utc).isoformat()
    candidate_id = candidate.get("candidate_id", "unknown")
    issuer = candidate.get("issuer", "unknown")
    currency_code = candidate.get("currency_code", "unknown")
    score_band = candidate.get("score_band", "low_attention")
    confidence = candidate.get("confidence", "low")
    risk_flags = candidate.get("risk_flags", [])
    meta_present = candidate.get("metadata_present", False)
    validated = candidate.get("validated_ledger_evidence", False)
    amm_present = candidate.get("amm_present", False)
    liquidity_strength = candidate.get("liquidity_signal_strength", "none")
    signal_types = candidate.get("source_signal_types", [])
    
    critical_warning = any(w.get("severity") == "critical" for w in drift_warnings)
    
    # Check if already holding
    if open_position is not None:
        if current_price_xrp is None:
            # We can't evaluate PnL, hold by default
            return PaperDecision(
                decision_id=_generate_decision_id(candidate_id, timestamp, "paper_hold"),
                candidate_id=candidate_id,
                issuer=issuer,
                currency_code=currency_code,
                action="paper_hold",
                reason="No current price to evaluate exit triggers.",
                confidence=confidence,
                metadata_present=meta_present,
                validated_ledger_evidence=validated,
                risk_flags=risk_flags,
                score_band=score_band,
                amm_present=amm_present,
                liquidity_signal_strength=liquidity_strength,
                source_signal_types=signal_types,
                timestamp=timestamp
            )
            
        entry_price = open_position.entry_price_xrp
        sl_price = entry_price * open_position.stop_loss_pct
        tp_price = entry_price * open_position.take_profit_pct
        
        exit_reason = None
        if current_price_xrp <= sl_price:
            exit_reason = "Stop loss hit"
        elif current_price_xrp >= tp_price:
            exit_reason = "Take profit hit"
        elif "POSSIBLE_SPAM_ISSUER" in risk_flags or critical_warning:
            exit_reason = "New critical risk or confidence decay"
            
        if exit_reason:
            return PaperDecision(
                decision_id=_generate_decision_id(candidate_id, timestamp, "paper_exit"),
                candidate_id=candidate_id,
                issuer=issuer,
                currency_code=currency_code,
                action="paper_exit",
                reason=exit_reason,
                confidence=confidence,
                metadata_present=meta_present,
                validated_ledger_evidence=validated,
                risk_flags=risk_flags,
                score_band=score_band,
                amm_present=amm_present,
                liquidity_signal_strength=liquidity_strength,
                source_signal_types=signal_types,
                timestamp=timestamp
            )
            
        return PaperDecision(
            decision_id=_generate_decision_id(candidate_id, timestamp, "paper_hold"),
            candidate_id=candidate_id,
            issuer=issuer,
            currency_code=currency_code,
            action="paper_hold",
            reason="No exit triggers met.",
            confidence=confidence,
            metadata_present=meta_present,
            validated_ledger_evidence=validated,
            risk_flags=risk_flags,
            score_band=score_band,
            amm_present=amm_present,
            liquidity_signal_strength=liquidity_strength,
            source_signal_types=signal_types,
            timestamp=timestamp
        )

    # Evaluate new entry
    reject_reason = None
    if not meta_present:
        reject_reason = "MISSING_METADATA dominates"
    elif not validated:
        reject_reason = "NO_VALIDATED_LEDGER_EVIDENCE"
    elif "offer_activity_low_confidence" in signal_types and "trustline_created" not in signal_types and not amm_present:
        reject_reason = "OFFER_ONLY_ACTIVITY"
    elif "POSSIBLE_SPAM_ISSUER" in risk_flags:
        reject_reason = "POSSIBLE_SPAM_ISSUER"
    elif liquidity_strength in ["none", "weak"] and not amm_present:
        reject_reason = "LOW_LIQUIDITY_SIGNAL"
    elif critical_warning:
        reject_reason = "critical Phase 33 warning exists"
    elif score_band not in ["review", "high_attention"]:
        reject_reason = "Candidate score too low"
    elif confidence not in ["medium", "high"]:
        reject_reason = "Confidence too low"
    elif current_open_positions_count >= max_positions:
        reject_reason = "Max positions exceeded"
        
    if reject_reason:
        return PaperDecision(
            decision_id=_generate_decision_id(candidate_id, timestamp, "paper_reject"),
            candidate_id=candidate_id,
            issuer=issuer,
            currency_code=currency_code,
            action="paper_reject",
            reason=reject_reason,
            confidence=confidence,
            metadata_present=meta_present,
            validated_ledger_evidence=validated,
            risk_flags=risk_flags,
            score_band=score_band,
            amm_present=amm_present,
            liquidity_signal_strength=liquidity_strength,
            source_signal_types=signal_types,
            timestamp=timestamp
        )
        
    return PaperDecision(
        decision_id=_generate_decision_id(candidate_id, timestamp, "paper_enter"),
        candidate_id=candidate_id,
        issuer=issuer,
        currency_code=currency_code,
        action="paper_enter",
        reason="Strong candidate passing all deterministic safety gates",
        confidence=confidence,
        metadata_present=meta_present,
        validated_ledger_evidence=validated,
        risk_flags=risk_flags,
        score_band=score_band,
        amm_present=amm_present,
        liquidity_signal_strength=liquidity_strength,
        source_signal_types=signal_types,
        timestamp=timestamp
    )
