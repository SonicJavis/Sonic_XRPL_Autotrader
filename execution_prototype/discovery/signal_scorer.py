from typing import List, Dict, Any
from execution_prototype.discovery.models import RawDiscoveryEvent

def calculate_score(events: List[RawDiscoveryEvent], risk_flags: List[str]) -> tuple[int, str]:
    trustline_score = 0
    amm_score = 0
    issuer_activity_score = 0
    metadata_quality_score = 0
    risk_penalty = 0
    
    trustlines = sum(1 for e in events if e.event_type == "trustline_created")
    if trustlines > 0:
        trustline_score = min(30, trustlines * 10)
        
    amms = sum(1 for e in events if e.event_type == "amm_created")
    if amms > 0:
        amm_score = min(30, amms * 30)
        
    issuer_act = sum(1 for e in events if e.event_type == "issuer_activity")
    if issuer_act > 0:
        issuer_activity_score = min(20, issuer_act * 10)
        
    meta_present = all(e.metadata_present for e in events)
    if meta_present and events:
        metadata_quality_score = 10
        
    if "MISSING_METADATA" in risk_flags:
        risk_penalty -= 20
    if "NO_VALIDATED_LEDGER_EVIDENCE" in risk_flags:
        risk_penalty -= 30
    if "OFFER_ONLY_ACTIVITY" in risk_flags:
        risk_penalty -= 10
        
    raw_score = trustline_score + amm_score + issuer_activity_score + metadata_quality_score + risk_penalty
    final_score = max(0, min(100, raw_score))
    
    if final_score <= 24:
        band = "ignore"
    elif final_score <= 49:
        band = "watch"
    elif final_score <= 74:
        band = "review"
    else:
        band = "high_attention"
        
    return final_score, band
