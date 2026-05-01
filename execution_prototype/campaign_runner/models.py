from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass(frozen=True, slots=True)
class CampaignRunState:
    campaign_id: str
    campaign_name: str
    started_at: str
    current_cycle: int
    max_cycles: int
    duration_days: int
    status: str  # active | halted | completed | insufficient_data
    latest_phase36_report: Optional[str]
    latest_phase37_report: Optional[str]
    latest_phase38_report: Optional[str]
    trust_score: Optional[int]
    governor_decision: Optional[str]
    protocol_context_flags: List[str]
    limitations: List[str]
    prohibited_live_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "started_at": self.started_at,
            "current_cycle": self.current_cycle,
            "max_cycles": self.max_cycles,
            "duration_days": self.duration_days,
            "status": self.status,
            "latest_phase36_report": self.latest_phase36_report,
            "latest_phase37_report": self.latest_phase37_report,
            "latest_phase38_report": self.latest_phase38_report,
            "trust_score": self.trust_score,
            "governor_decision": self.governor_decision,
            "protocol_context_flags": self.protocol_context_flags,
            "limitations": self.limitations,
            "prohibited_live_action": self.prohibited_live_action
        }

@dataclass(frozen=True, slots=True)
class CampaignCycleResult:
    cycle_id: str
    campaign_id: str
    cycle_number: int
    cycle_time: str
    discovery_report_path: Optional[str]
    paper_report_path: Optional[str]
    review_report_path: Optional[str]
    strategy_report_path: Optional[str]
    risk_report_path: Optional[str]
    governor_decision: str
    trust_score: Optional[int]
    positions_opened: int
    positions_closed: int
    paper_pnl_xrp: Optional[float]
    warnings: List[str]
    protocol_context_flags: List[str]
    next_required_action: str
    prohibited_live_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "campaign_id": self.campaign_id,
            "cycle_number": self.cycle_number,
            "cycle_time": self.cycle_time,
            "discovery_report_path": self.discovery_report_path,
            "paper_report_path": self.paper_report_path,
            "review_report_path": self.review_report_path,
            "strategy_report_path": self.strategy_report_path,
            "risk_report_path": self.risk_report_path,
            "governor_decision": self.governor_decision,
            "trust_score": self.trust_score,
            "positions_opened": self.positions_opened,
            "positions_closed": self.positions_closed,
            "paper_pnl_xrp": self.paper_pnl_xrp,
            "warnings": self.warnings,
            "protocol_context_flags": self.protocol_context_flags,
            "next_required_action": self.next_required_action,
            "prohibited_live_action": self.prohibited_live_action
        }

@dataclass(frozen=True, slots=True)
class CampaignDashboardData:
    campaign: Dict[str, Any]
    latest_cycle: Dict[str, Any]
    trust_score: Optional[int]
    governor_decision: str
    paper_summary: Dict[str, Any]
    strategy_summary: Dict[str, Any]
    risk_summary: Dict[str, Any]
    trade_journal_preview: List[Dict[str, Any]]
    protocol_context: List[str]
    limitations: List[str]
    safety_statement: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign": self.campaign,
            "latest_cycle": self.latest_cycle,
            "trust_score": self.trust_score,
            "governor_decision": self.governor_decision,
            "paper_summary": self.paper_summary,
            "strategy_summary": self.strategy_summary,
            "risk_summary": self.risk_summary,
            "trade_journal_preview": self.trade_journal_preview,
            "protocol_context": self.protocol_context,
            "limitations": self.limitations,
            "safety_statement": self.safety_statement
        }
