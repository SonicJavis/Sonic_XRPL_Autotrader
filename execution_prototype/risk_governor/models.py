from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class OperatorTrustScore:
    trust_score_id: str
    overall_score: int
    data_quality_score: int
    strategy_quality_score: int
    drift_stability_score: int
    paper_performance_score: int
    metadata_completeness_score: int
    validation_integrity_score: int
    protocol_risk_score: int
    confidence_band: str
    limitations: List[str]
    evidence_hash: str
    prohibited_live_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trust_score_id": self.trust_score_id,
            "overall_score": self.overall_score,
            "data_quality_score": self.data_quality_score,
            "strategy_quality_score": self.strategy_quality_score,
            "drift_stability_score": self.drift_stability_score,
            "paper_performance_score": self.paper_performance_score,
            "metadata_completeness_score": self.metadata_completeness_score,
            "validation_integrity_score": self.validation_integrity_score,
            "protocol_risk_score": self.protocol_risk_score,
            "confidence_band": self.confidence_band,
            "limitations": self.limitations,
            "evidence_hash": self.evidence_hash,
            "prohibited_live_action": self.prohibited_live_action
        }

@dataclass(frozen=True, slots=True)
class RiskRuleResult:
    rule_result_id: str
    rule_id: str
    rule_name: str
    passed: bool
    severity: str
    evidence: List[str]
    recommended_action: str
    prohibited_auto_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_result_id": self.rule_result_id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "passed": self.passed,
            "severity": self.severity,
            "evidence": self.evidence,
            "recommended_action": self.recommended_action,
            "prohibited_auto_action": self.prohibited_auto_action
        }

@dataclass(frozen=True, slots=True)
class RiskGovernorDecision:
    decision_id: str
    campaign_id: Optional[str]
    decision: str
    trust_score: int
    risk_score: int
    triggered_rules: List[str]
    evidence: List[str]
    required_human_action: str
    prohibited_live_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "campaign_id": self.campaign_id,
            "decision": self.decision,
            "trust_score": self.trust_score,
            "risk_score": self.risk_score,
            "triggered_rules": self.triggered_rules,
            "evidence": self.evidence,
            "required_human_action": self.required_human_action,
            "prohibited_live_action": self.prohibited_live_action
        }
