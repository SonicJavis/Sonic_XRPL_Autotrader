from typing import List
from execution_prototype.discovery.models import RawDiscoveryEvent

def generate_risk_flags(events: List[RawDiscoveryEvent]) -> List[str]:
    flags = []
    
    if any(not e.metadata_present for e in events):
        flags.append("MISSING_METADATA")
        
    if all(not e.validated for e in events):
        flags.append("NO_VALIDATED_LEDGER_EVIDENCE")
        
    event_types = set(e.event_type for e in events)
    
    if event_types == {"offer_activity_low_confidence"}:
        flags.append("OFFER_ONLY_ACTIVITY")
        
    if "amm_created" not in event_types:
        flags.append("AMM_NOT_PRESENT")
        
    trustlines = sum(1 for e in events if e.event_type == "trustline_created")
    if trustlines == 1:
        flags.append("SINGLE_TRUSTLINE_ONLY")
        
    return flags
