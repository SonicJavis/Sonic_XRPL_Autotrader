from typing import Dict, Optional
import hashlib
from datetime import datetime, timezone
from execution_prototype.paper_operator.models import PaperLedgerState, PaperPosition, PaperDecision

def initialize_ledger(campaign_id: str, starting_balance: float = 1000.0, max_positions: int = 5) -> PaperLedgerState:
    return PaperLedgerState(
        campaign_id=campaign_id,
        balance_xrp=starting_balance,
        open_positions={},
        max_positions=max_positions
    )

def _generate_position_id(decision_id: str, candidate_id: str) -> str:
    basis = f"{decision_id}|{candidate_id}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def apply_decision(ledger: PaperLedgerState, decision: PaperDecision, current_price_xrp: Optional[float] = None) -> tuple[PaperLedgerState, Optional[PaperPosition], Optional[PaperPosition]]:
    """
    Applies a decision to the ledger.
    Returns: (new_ledger_state, closed_position_if_any, opened_position_if_any)
    """
    open_positions = dict(ledger.open_positions)
    balance_xrp = ledger.balance_xrp
    
    closed_pos = None
    opened_pos = None
    
    if decision.action == "paper_enter":
        if decision.candidate_id not in open_positions and len(open_positions) < ledger.max_positions and current_price_xrp is not None:
            # We open a position
            size_xrp = balance_xrp * 0.1 # 10% of portfolio per trade
            if size_xrp > balance_xrp:
                size_xrp = balance_xrp
                
            pos = PaperPosition(
                position_id=_generate_position_id(decision.decision_id, decision.candidate_id),
                candidate_id=decision.candidate_id,
                issuer=decision.issuer,
                currency_code=decision.currency_code,
                entry_price_xrp=current_price_xrp,
                size_xrp=size_xrp,
                entry_decision_id=decision.decision_id,
                entry_timestamp=datetime.now(timezone.utc).isoformat()
            )
            open_positions[decision.candidate_id] = pos
            balance_xrp -= size_xrp
            opened_pos = pos
            
    elif decision.action == "paper_exit":
        if decision.candidate_id in open_positions and current_price_xrp is not None:
            pos = open_positions.pop(decision.candidate_id)
            
            # calculate PnL
            # Assuming Long position
            pnl_xrp = ((current_price_xrp - pos.entry_price_xrp) / pos.entry_price_xrp) * pos.size_xrp
            balance_xrp += pos.size_xrp + pnl_xrp
            closed_pos = pos
            
    new_ledger = PaperLedgerState(
        campaign_id=ledger.campaign_id,
        balance_xrp=balance_xrp,
        open_positions=open_positions,
        max_positions=ledger.max_positions
    )
    
    return new_ledger, closed_pos, opened_pos
