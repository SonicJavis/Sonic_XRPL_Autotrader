import hashlib
from typing import List, Dict, Any
from execution_prototype.discovery.models import RawDiscoveryEvent, MemeCandidate
from execution_prototype.discovery.signal_scorer import calculate_score
from execution_prototype.discovery.risk_classifier import generate_risk_flags

def _generate_candidate_id(issuer: str, currency: str) -> str:
    basis = f"{issuer}|{currency}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def _determine_confidence(events: List[RawDiscoveryEvent], risk_flags: List[str]) -> str:
    types = set(e.event_type for e in events)
    trustlines = sum(1 for e in events if e.event_type == "trustline_created")
    
    if "MISSING_METADATA" in risk_flags or "NO_VALIDATED_LEDGER_EVIDENCE" in risk_flags:
        return "low"
        
    if "amm_created" in types or trustlines > 1:
        return "high"
        
    if trustlines == 1 or "issuer_activity" in types:
        return "medium"
        
    return "low"

def build_candidates(events: List[RawDiscoveryEvent]) -> List[MemeCandidate]:
    # Group by issuer + currency
    groups: Dict[tuple[str, str], List[RawDiscoveryEvent]] = {}
    
    for e in events:
        key = (e.issuer, e.currency_code)
        if key not in groups:
            groups[key] = []
        groups[key].append(e)
        
    candidates = []
    
    for (issuer, currency), group_events in groups.items():
        types = set(e.event_type for e in group_events)
        
        # Signal Rules:
        # >= 1 strong signal OR >= 2 weak signals
        strong_signals = sum(1 for e in group_events if e.event_type in ["trustline_created", "amm_created"])
        weak_signals = sum(1 for e in group_events if e.event_type in ["offer_activity_low_confidence", "issuer_activity"])
        
        if strong_signals < 1 and weak_signals < 2:
            continue
            
        risk_flags = generate_risk_flags(group_events)
        score, band = calculate_score(group_events, risk_flags)
        confidence = _determine_confidence(group_events, risk_flags)
        
        first_ledger = min(e.ledger_index for e in group_events)
        event_ids = sorted(e.event_id for e in group_events)
        
        cand = MemeCandidate(
            candidate_id=_generate_candidate_id(issuer, currency),
            issuer=issuer,
            currency_code=currency,
            first_seen_ledger=first_ledger,
            evidence_event_ids=event_ids,
            signal_summary=f"Found {strong_signals} strong and {weak_signals} weak signals.",
            confidence=confidence,
            risk_flags=risk_flags,
            score=score,
            score_band=band
        )
        candidates.append(cand)
        
    return candidates
