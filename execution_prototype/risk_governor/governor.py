from typing import List, Optional
import hashlib
from execution_prototype.risk_governor.models import OperatorTrustScore, RiskRuleResult, RiskGovernorDecision

def _generate_decision_id(trust_id: str, campaign_id: str) -> str:
    basis = f"{trust_id}|{campaign_id}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def make_governor_decision(
    trust_score: OperatorTrustScore,
    rule_results: List[RiskRuleResult],
    campaign_id: Optional[str]
) -> RiskGovernorDecision:
    
    # Base decision
    decision = "allow_paper"
    required_human_action = "None"
    triggered_rules = []
    evidence = []
    
    for rule in rule_results:
        if not rule.passed:
            triggered_rules.append(rule.rule_id)
            if rule.severity == "critical" and rule.rule_id != "RULE_LIVE_1":
                decision = "halt_paper"
                evidence.extend(rule.evidence)
            elif rule.severity == "warning" and decision != "halt_paper":
                decision = "reduce_paper_risk"
                evidence.extend(rule.evidence)
                
    if decision != "halt_paper":
        if trust_score.overall_score < 40:
            decision = "halt_paper"
            evidence.append(f"Trust score {trust_score.overall_score} < 40")
        elif trust_score.overall_score < 60:
            decision = "reduce_paper_risk"
            evidence.append(f"Trust score {trust_score.overall_score} < 60")
            
    if "insufficient_data" in trust_score.limitations or any("No candidates" in l for l in trust_score.limitations):
        decision = "insufficient_data"
        evidence.append("Missing required input data.")
        
    if decision == "halt_paper":
        required_human_action = "Review critical failures and system state."
    elif decision == "reduce_paper_risk":
        required_human_action = "Review warnings and monitor closely."
        
    decision_id = _generate_decision_id(trust_score.trust_score_id, campaign_id or "none")
    
    return RiskGovernorDecision(
        decision_id=decision_id,
        campaign_id=campaign_id,
        decision=decision,
        trust_score=trust_score.overall_score,
        risk_score=max(0, 100 - len(triggered_rules) * 10),
        triggered_rules=triggered_rules,
        evidence=list(set(evidence)) if evidence else ["All checks passed"],
        required_human_action=required_human_action,
        prohibited_live_action="Live execution strictly prohibited."
    )
