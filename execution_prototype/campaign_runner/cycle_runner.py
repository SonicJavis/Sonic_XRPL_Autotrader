import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone
import hashlib

from execution_prototype.campaign_runner.models import CampaignRunState, CampaignCycleResult
from execution_prototype.campaign_runner.state_store import update_campaign_state

def _generate_cycle_id(campaign_id: str, cycle_number: int) -> str:
    basis = f"{campaign_id}|{cycle_number}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def run_cycle(
    state: CampaignRunState,
    discovery_report: Path,
    output_dir: Path,
    phase33_report: Path,
    starting_balance: float
) -> tuple[CampaignRunState, CampaignCycleResult]:
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cycle_num = state.current_cycle + 1
    cycle_out_dir = output_dir / state.campaign_id / f"cycle_{cycle_num}_{timestamp}"
    cycle_out_dir.mkdir(parents=True, exist_ok=True)
    
    p36_dir = cycle_out_dir / "phase36"
    p37_dir = cycle_out_dir / "phase37"
    p38_dir = cycle_out_dir / "phase38"
    
    # 1. Run Phase 36 (Paper Operator)
    cmd36 = [
        sys.executable, "-m", "execution_prototype.pipeline.cli",
        "--discovery-report", str(discovery_report),
        "--output-dir", str(p36_dir),
        "--duration-days", "1",
        "--run-review"
    ]
    if state.latest_phase36_report:
        # If we have a previous state, we'd pass it here, but pipeline.cli currently starts fresh or loads a specific one.
        # For this prototype, we'll just run it. The actual paper operator handles its own persistence in theory, or we chain it.
        # We will just pass the new directory.
        pass
        
    subprocess.run(cmd36, check=False)
    
    # Check if p36 generated output
    actual_p36 = None
    if p36_dir.exists() and list(p36_dir.glob("*")):
        # Get latest timestamp dir in p36
        subdirs = sorted([d for d in p36_dir.iterdir() if d.is_dir()])
        if subdirs:
            actual_p36 = subdirs[-1]
            
    # 2. Run Phase 37 (Strategy Performance)
    actual_p37 = None
    if actual_p36:
        cmd37 = [
            sys.executable, "-m", "execution_prototype.strategy_performance.cli",
            "--paper-report", str(actual_p36),
            "--discovery-report", str(discovery_report),
            "--output-dir", str(p37_dir)
        ]
        subprocess.run(cmd37, check=False)
        subdirs = sorted([d for d in p37_dir.iterdir() if d.is_dir()])
        if subdirs:
            actual_p37 = subdirs[-1]
            
    # 3. Run Phase 38 (Risk Governor)
    actual_p38 = None
    governor_decision = "insufficient_data"
    trust_score = None
    
    if actual_p36 and actual_p37:
        cmd38 = [
            sys.executable, "-m", "execution_prototype.risk_governor.cli",
            "--phase36-report", str(actual_p36),
            "--phase37-report", str(actual_p37),
            "--output-dir", str(p38_dir)
        ]
        if phase33_report:
            cmd38.extend(["--phase33-report", str(phase33_report)])
            
        subprocess.run(cmd38, check=False)
        subdirs = sorted([d for d in p38_dir.iterdir() if d.is_dir()])
        if subdirs:
            actual_p38 = subdirs[-1]
            # Parse governor result
            import json
            gov_file = actual_p38 / "risk_governor_decision.json"
            if gov_file.exists():
                with open(gov_file, "r") as f:
                    gdata = json.load(f)
                    governor_decision = gdata.get("decision", "insufficient_data")
                    trust_score = gdata.get("trust_score")
                    
    new_status = "active"
    if governor_decision == "halt_paper":
        new_status = "halted"
    elif governor_decision == "insufficient_data":
        # Keep active, but log limitation
        pass
        
    new_state = update_campaign_state(
        state, new_status, governor_decision, trust_score,
        str(actual_p36) if actual_p36 else None,
        str(actual_p37) if actual_p37 else None,
        str(actual_p38) if actual_p38 else None
    )
    
    # We don't parse full PnL here, we leave it to summary builder, but we stub it for the cycle result
    result = CampaignCycleResult(
        cycle_id=_generate_cycle_id(state.campaign_id, cycle_num),
        campaign_id=state.campaign_id,
        cycle_number=cycle_num,
        cycle_time=timestamp,
        discovery_report_path=str(discovery_report),
        paper_report_path=str(actual_p36) if actual_p36 else None,
        review_report_path=str(actual_p36) if actual_p36 else None, # Phase 36 pipeline puts review inside its output
        strategy_report_path=str(actual_p37) if actual_p37 else None,
        risk_report_path=str(actual_p38) if actual_p38 else None,
        governor_decision=governor_decision,
        trust_score=trust_score,
        positions_opened=0, # Stub
        positions_closed=0, # Stub
        paper_pnl_xrp=0.0, # Stub
        warnings=[],
        protocol_context_flags=[],
        next_required_action="Review campaign dashboard." if new_status == "halted" else "Continue to next cycle.",
        prohibited_live_action="Live execution strictly prohibited."
    )
    
    return new_state, result
