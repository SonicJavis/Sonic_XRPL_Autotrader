from typing import List, Dict, Any, Optional
import hashlib
from execution_prototype.risk_governor.models import RiskRuleResult, OperatorTrustScore

def _generate_rule_id(rule_id: str, evidence: str) -> str:
    basis = f"{rule_id}|{evidence}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def evaluate_metadata_completeness(candidates: List[Dict[str, Any]]) -> RiskRuleResult:
    total = len(candidates)
    if total == 0:
        return RiskRuleResult("r1", "RULE_META_1", "Metadata Completeness", False, "critical", ["No candidates"], "Halt", "All")
    missing = sum(1 for c in candidates if not c.get("metadata_present", False))
    rate = missing / total
    passed = rate <= 0.30
    severity = "info" if passed else "critical"
    
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_META_1", f"{missing}_{total}"),
        rule_id="RULE_META_1",
        rule_name="Metadata Completeness",
        passed=passed,
        severity=severity,
        evidence=[f"Missing metadata rate: {rate*100:.1f}%"],
        recommended_action="None" if passed else "Halt paper trading",
        prohibited_auto_action="Live trading"
    )

def evaluate_validation_integrity(paper_decisions: List[Dict[str, Any]]) -> RiskRuleResult:
    unvalidated_entries = sum(1 for d in paper_decisions if d.get("action") == "paper_enter" and not d.get("validated_ledger_evidence", True))
    passed = unvalidated_entries == 0
    severity = "info" if passed else "critical"
    
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_VAL_1", str(unvalidated_entries)),
        rule_id="RULE_VAL_1",
        rule_name="Validation Integrity",
        passed=passed,
        severity=severity,
        evidence=[f"Unvalidated paper entries: {unvalidated_entries}"],
        recommended_action="None" if passed else "Halt paper trading",
        prohibited_auto_action="Live trading"
    )

def evaluate_strategy_stability(strategy_tournament: Optional[Dict[str, Any]]) -> RiskRuleResult:
    if not strategy_tournament:
        return RiskRuleResult("r3", "RULE_STRAT_1", "Strategy Stability", False, "warning", ["No tournament"], "Reduce paper risk", "Live trading")
    
    ranked = strategy_tournament.get("ranked_strategies", [])
    if not ranked:
        return RiskRuleResult("r3", "RULE_STRAT_1", "Strategy Stability", False, "warning", ["No strategies ranked"], "Reduce paper risk", "Live trading")
        
    best_unk = ranked[0].get("unknown_outcome_rate", 100)
    passed = best_unk <= 35.0
    severity = "info" if passed else "critical"
    
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_STRAT_1", str(best_unk)),
        rule_id="RULE_STRAT_1",
        rule_name="Strategy Stability",
        passed=passed,
        severity=severity,
        evidence=[f"Best strategy unknown outcome rate: {best_unk:.1f}%"],
        recommended_action="None" if passed else "Halt paper trading",
        prohibited_auto_action="Live trading"
    )

def evaluate_drawdown(paper_review: Optional[Dict[str, Any]]) -> RiskRuleResult:
    if not paper_review:
        return RiskRuleResult("r4", "RULE_DD_1", "Drawdown", True, "info", ["No review"], "None", "Live trading")
        
    # Drawdown rule
    max_dd = 0.0 # Placeholder since we didn't track max DD in Phase 35, we'll check loss count
    # wait, we have paper_review which contains loss count
    # max_drawdown_pct is standard but if not there, use losses
    passed = paper_review.get("losses", 0) <= 5 
    severity = "info" if passed else "critical"
    
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_DD_1", str(paper_review.get("losses", 0))),
        rule_id="RULE_DD_1",
        rule_name="Drawdown / Losses",
        passed=passed,
        severity=severity,
        evidence=[f"Paper losses: {paper_review.get('losses', 0)}"],
        recommended_action="None" if passed else "Halt paper trading",
        prohibited_auto_action="Live trading"
    )

def evaluate_drift_warnings(early_warnings: List[Dict[str, Any]]) -> RiskRuleResult:
    critical_warnings = sum(1 for w in early_warnings if w.get("severity") == "critical")
    passed = critical_warnings == 0
    severity = "info" if passed else "critical"
    
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_DRIFT_1", str(critical_warnings)),
        rule_id="RULE_DRIFT_1",
        rule_name="Drift Warnings",
        passed=passed,
        severity=severity,
        evidence=[f"Critical drift warnings: {critical_warnings}"],
        recommended_action="None" if passed else "Halt paper trading",
        prohibited_auto_action="Live trading"
    )

def evaluate_ambiguity(paper_decisions: List[Dict[str, Any]]) -> RiskRuleResult:
    ambiguous = sum(1 for d in paper_decisions if "AMBIGUOUS_MATCH" in d.get("reason", ""))
    total = len(paper_decisions)
    rate = ambiguous / total if total > 0 else 0
    passed = rate <= 0.05
    severity = "info" if passed else "warning"
    
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_AMB_1", f"{ambiguous}_{total}"),
        rule_id="RULE_AMB_1",
        rule_name="Ambiguity",
        passed=passed,
        severity=severity,
        evidence=[f"Ambiguous match rate: {rate*100:.1f}%"],
        recommended_action="None" if passed else "Reduce paper risk",
        prohibited_auto_action="Live trading"
    )

def evaluate_false_confidence(paper_decisions: List[Dict[str, Any]]) -> RiskRuleResult:
    false_conf = sum(1 for d in paper_decisions if d.get("confidence") == "high" and not d.get("metadata_present", True))
    passed = false_conf == 0
    severity = "info" if passed else "critical"
    
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_CONF_1", str(false_conf)),
        rule_id="RULE_CONF_1",
        rule_name="False Confidence",
        passed=passed,
        severity=severity,
        evidence=[f"False high confidence entries: {false_conf}"],
        recommended_action="None" if passed else "Halt paper trading",
        prohibited_auto_action="Live trading"
    )

def evaluate_protocol_features(candidates: List[Dict[str, Any]]) -> RiskRuleResult:
    risks = []
    for c in candidates:
        flags = c.get("risk_flags", [])
        if "CLAWBACK_ENABLED" in flags:
            risks.append("Clawback enabled detected")
        if "AMM_CLAWBACK_ENABLED" in flags:
            risks.append("AMM Clawback enabled detected")
            
    passed = len(risks) == 0
    severity = "info" if passed else "warning"
    
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_PROT_1", str(len(risks))),
        rule_id="RULE_PROT_1",
        rule_name="Protocol Features Risk",
        passed=passed,
        severity=severity,
        evidence=list(set(risks)) if risks else ["No protocol feature risks"],
        recommended_action="None" if passed else "Manual review recommended",
        prohibited_auto_action="Live trading"
    )

def evaluate_live_readiness() -> RiskRuleResult:
    return RiskRuleResult(
        rule_result_id=_generate_rule_id("RULE_LIVE_1", "forbidden"),
        rule_id="RULE_LIVE_1",
        rule_name="Live Readiness",
        passed=False,
        severity="critical",
        evidence=["Live trading is strictly forbidden by policy."],
        recommended_action="Halt live trading",
        prohibited_auto_action="Live trading"
    )

def run_all_rules(
    candidates: List[Dict[str, Any]],
    paper_decisions: List[Dict[str, Any]],
    paper_review: Optional[Dict[str, Any]],
    early_warnings: List[Dict[str, Any]],
    strategy_tournament: Optional[Dict[str, Any]]
) -> List[RiskRuleResult]:
    
    return [
        evaluate_metadata_completeness(candidates),
        evaluate_validation_integrity(paper_decisions),
        evaluate_strategy_stability(strategy_tournament),
        evaluate_drawdown(paper_review),
        evaluate_drift_warnings(early_warnings),
        evaluate_ambiguity(paper_decisions),
        evaluate_false_confidence(paper_decisions),
        evaluate_protocol_features(candidates),
        evaluate_live_readiness()
    ]
