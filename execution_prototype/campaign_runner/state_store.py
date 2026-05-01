import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from execution_prototype.campaign_runner.models import CampaignRunState

def _generate_campaign_id(name: str) -> str:
    basis = f"campaign|{name}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def load_campaign_state(output_dir: Path, campaign_id: str) -> Optional[CampaignRunState]:
    state_file = output_dir / campaign_id / "campaign_state.json"
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return CampaignRunState(**data)
    return None

def create_initial_campaign(campaign_name: str, duration_days: int) -> CampaignRunState:
    camp_id = _generate_campaign_id(campaign_name)
    return CampaignRunState(
        campaign_id=camp_id,
        campaign_name=campaign_name,
        started_at=datetime.now(timezone.utc).isoformat(),
        current_cycle=0,
        max_cycles=duration_days, # 1 cycle per day
        duration_days=duration_days,
        status="active",
        latest_phase36_report=None,
        latest_phase37_report=None,
        latest_phase38_report=None,
        trust_score=None,
        governor_decision=None,
        protocol_context_flags=[],
        limitations=[],
        prohibited_live_action="Live execution strictly prohibited."
    )

def update_campaign_state(
    state: CampaignRunState, 
    new_status: str, 
    governor_decision: str, 
    trust_score: Optional[int],
    p36: Optional[str],
    p37: Optional[str],
    p38: Optional[str]
) -> CampaignRunState:
    new_cycle = state.current_cycle + 1
    if new_status == "active" and new_cycle >= state.max_cycles:
        new_status = "completed"
        
    return CampaignRunState(
        campaign_id=state.campaign_id,
        campaign_name=state.campaign_name,
        started_at=state.started_at,
        current_cycle=new_cycle,
        max_cycles=state.max_cycles,
        duration_days=state.duration_days,
        status=new_status,
        latest_phase36_report=p36 or state.latest_phase36_report,
        latest_phase37_report=p37 or state.latest_phase37_report,
        latest_phase38_report=p38 or state.latest_phase38_report,
        trust_score=trust_score,
        governor_decision=governor_decision,
        protocol_context_flags=state.protocol_context_flags,
        limitations=state.limitations,
        prohibited_live_action=state.prohibited_live_action
    )
