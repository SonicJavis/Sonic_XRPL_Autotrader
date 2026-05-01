import hashlib
import json
from typing import Dict, Any, List, Tuple
from execution_prototype.risk_governor.models import OperatorTrustScore

def _generate_trust_score_id(components: Dict[str, Any]) -> str:
    basis = json.dumps(components, sort_keys=True)
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def _bound(val: float) -> int:
    return max(0, min(100, int(val)))

def calculate_trust_score(
    candidates: List[Dict[str, Any]],
    paper_trades: List[Dict[str, Any]],
    paper_decisions: List[Dict[str, Any]],
    paper_review: Optional[Dict[str, Any]],
    early_warnings: List[Dict[str, Any]],
    strategy_backtests: List[Dict[str, Any]],
    strategy_tournament: Optional[Dict[str, Any]]
) -> OperatorTrustScore:
    
    limitations = []
    
    # 1. Metadata Completeness
    total_candidates = len(candidates)
    if total_candidates == 0:
        meta_score = 0
        limitations.append("No candidates provided for metadata check.")
    else:
        has_meta = sum(1 for c in candidates if c.get("metadata_present", False))
        meta_score = _bound((has_meta / total_candidates) * 100.0)

    # 2. Validation Integrity
    total_decisions = len(paper_decisions)
    if total_decisions == 0:
        val_score = 0
        limitations.append("No paper decisions provided for validation integrity.")
    else:
        unvalidated = sum(1 for d in paper_decisions if "NO_VALIDATED_LEDGER_EVIDENCE" in d.get("reason", ""))
        # If any are unvalidated entries, penalize heavily. 
        # But wait, reason usually has "NO_VALIDATED_LEDGER_EVIDENCE" when rejected.
        # We want to check if any paper_enter had NO validated evidence.
        unvalidated_entries = sum(1 for d in paper_decisions if d.get("action") == "paper_enter" and not d.get("validated_ledger_evidence", True))
        if unvalidated_entries > 0:
            val_score = 0
            limitations.append(f"Found {unvalidated_entries} unvalidated entries.")
        else:
            val_score = 100

    # 3. Data Quality Score
    dq_score = (meta_score + val_score) / 2
    if len(paper_trades) == 0:
        dq_score -= 20
        limitations.append("No paper trades available for data quality.")

    # 4. Strategy Quality Score
    if not strategy_tournament or not strategy_backtests:
        strat_score = 0
        limitations.append("No strategy tournament results available.")
    else:
        ranked = strategy_tournament.get("ranked_strategies", [])
        if not ranked:
            strat_score = 0
        else:
            best_score = ranked[0].get("risk_adjusted_score", 0)
            strat_score = _bound(best_score)
            
            # Penalize if high unknown outcome rate in best
            best_unk = ranked[0].get("unknown_outcome_rate", 100)
            if best_unk > 35:
                strat_score -= 20
                limitations.append(f"Best strategy has high unknown outcome rate ({best_unk}%).")

    # 5. Drift Stability Score
    critical_warnings = sum(1 for w in early_warnings if w.get("severity") == "critical")
    if critical_warnings > 0:
        drift_score = 0
        limitations.append(f"Found {critical_warnings} critical drift warnings.")
    else:
        drift_score = max(0, 100 - len(early_warnings) * 5)

    # 6. Paper Performance Score
    if not paper_review:
        perf_score = 0
        limitations.append("No paper performance review available.")
    else:
        win_rate = paper_review.get("win_rate")
        if win_rate is None:
            perf_score = 0
            limitations.append("Win rate is unknown.")
        else:
            perf_score = _bound(win_rate)
            losses = paper_review.get("losses", 0)
            if losses > 3:
                perf_score -= 20
            
    # 7. Protocol Risk Score
    protocol_score = 100
    protocol_risks = 0
    for cand in candidates:
        flags = cand.get("risk_flags", [])
        if "CLAWBACK_ENABLED" in flags or "AMM_CLAWBACK_ENABLED" in flags or "FREEZE_ENABLED" in flags:
            protocol_risks += 1
            
    if total_candidates > 0:
        risk_rate = protocol_risks / total_candidates
        protocol_score = _bound(100 - (risk_rate * 100))

    # Overall Score Calculation
    overall = (
        dq_score * 0.15 +
        strat_score * 0.20 +
        drift_score * 0.15 +
        perf_score * 0.20 +
        meta_score * 0.15 +
        val_score * 0.10 +
        protocol_score * 0.05
    )
    overall_bound = _bound(overall)
    
    # Caps
    if meta_score < 70:
        overall_bound = min(overall_bound, 59)
    if strat_score == 0 and strategy_tournament:
        overall_bound = min(overall_bound, 39)
    if drift_score == 0:
        overall_bound = min(overall_bound, 39)
    if val_score == 0:
        overall_bound = min(overall_bound, 39)
        
    # High confidence false check
    false_confidence = 0
    for d in paper_decisions:
        if d.get("confidence") == "high" and not d.get("metadata_present", True):
            false_confidence += 1
            
    if false_confidence > 0:
        overall_bound = min(overall_bound, 39)
        limitations.append(f"Found {false_confidence} false confidence entries.")

    if overall_bound < 40:
        confidence_band = "low"
    elif overall_bound < 60:
        confidence_band = "medium"
    else:
        confidence_band = "high"

    evidence_hash = _generate_trust_score_id({
        "dq": dq_score,
        "strat": strat_score,
        "drift": drift_score,
        "perf": perf_score,
        "meta": meta_score,
        "val": val_score,
        "prot": protocol_score
    })
    
    limitations.append("Relies on offline fixtures.")

    return OperatorTrustScore(
        trust_score_id=evidence_hash,
        overall_score=overall_bound,
        data_quality_score=_bound(dq_score),
        strategy_quality_score=strat_score,
        drift_stability_score=drift_score,
        paper_performance_score=perf_score,
        metadata_completeness_score=meta_score,
        validation_integrity_score=val_score,
        protocol_risk_score=protocol_score,
        confidence_band=confidence_band,
        limitations=limitations,
        evidence_hash=evidence_hash,
        prohibited_live_action="Live execution strictly prohibited."
    )
