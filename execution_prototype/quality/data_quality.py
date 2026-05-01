from typing import Dict, Any, List

def check_candidate_quality(candidate: Dict[str, Any]) -> List[str]:
    errors = []
    
    if not candidate.get("candidate_id"):
        errors.append("Candidate ID missing")
    if not candidate.get("issuer") or not candidate.get("currency_code"):
        errors.append("Issuer or Currency Code missing")
    if candidate.get("score_band") not in ["low_attention", "review", "high_attention"]:
        errors.append("Invalid score band")
    if candidate.get("confidence") == "high" and not candidate.get("metadata_present"):
        errors.append("High confidence claimed without metadata")
        
    return errors

def check_paper_entry_quality(candidate: Dict[str, Any]) -> List[str]:
    errors = check_candidate_quality(candidate)
    
    if not candidate.get("validated_ledger_evidence"):
        errors.append("Validated ledger evidence missing for paper entry")
        
    return errors

def check_pnl_quality(entry_price: float, exit_price: float) -> List[str]:
    errors = []
    if entry_price is None or exit_price is None:
        errors.append("Fake PnL detected: price is missing")
    return errors
