from typing import Dict, Any, List
import hashlib

def _generate_evaluation_id(strategy_id: str, candidate_id: str) -> str:
    basis = f"{strategy_id}|{candidate_id}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

# Strategies

def trustline_spike_watch(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    signals = candidate.get("source_signal_types", [])
    if "trustline_created" in signals:
        return True, "Trustline spike detected", ["trustlines"]
    return False, "No trustline spike", []

def amm_seeded_launch_watch(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    if candidate.get("amm_present", False):
        return True, "AMM creation detected", ["AMM"]
    return False, "No AMM evidence", []

def metadata_backed_high_attention(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    if candidate.get("score_band") == "high_attention" and candidate.get("metadata_present", False):
        return True, "High attention with metadata", ["metadata"]
    return False, "Lacks high attention or metadata", []

def avoid_offer_only_noise(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    signals = candidate.get("source_signal_types", [])
    has_offer = "offer_activity_low_confidence" in signals or "OfferCreate" in signals
    has_trustline = "trustline_created" in signals
    has_amm = candidate.get("amm_present", False)
    
    if has_offer and not has_trustline and not has_amm:
        return False, "Rejected: OfferOnly noise", ["OfferCreate"]
    if has_trustline or has_amm:
        return True, "Passed OfferOnly filter (has trustline/amm)", []
    return False, "No meaningful activity", []

def early_but_validated_watch(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    if candidate.get("validated_ledger_evidence", False) and candidate.get("score_band") in ["review", "high_attention"]:
        return True, "Early candidate but validated on ledger", ["validated_ledger"]
    return False, "Not early or not validated", []

def liquidity_first_watch(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    strength = candidate.get("liquidity_signal_strength", "none")
    if strength in ["medium", "strong"] or candidate.get("amm_present", False):
        return True, "Strong liquidity or AMM", ["liquidity", "AMM"]
    return False, "Weak liquidity", []

def conservative_metadata_only(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    if candidate.get("metadata_present", False) and candidate.get("validated_ledger_evidence", False) and "POSSIBLE_SPAM_ISSUER" not in candidate.get("risk_flags", []):
        return True, "Conservative metadata and validated evidence", ["metadata", "validated_ledger"]
    return False, "Missing strict conservative criteria", []

def aggressive_high_attention_paper_only(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    if candidate.get("score_band") == "high_attention":
        return True, "Aggressive high attention entry", []
    return False, "Not high attention", []

def clawback_risk_avoidance(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    risk_flags = candidate.get("risk_flags", [])
    # In a real scenario, this would detect tfAllowTrustLineClawback or AMMClawback
    if "CLAWBACK_ENABLED" in risk_flags or "AMM_CLAWBACK_ENABLED" in risk_flags:
        return False, "Clawback enabled, avoiding", ["Clawback"]
    return True, "No clawback detected", ["Clawback"]

def mpt_feature_watch(candidate: Dict[str, Any]) -> tuple[bool, str, List[str]]:
    signals = candidate.get("source_signal_types", [])
    if "MPT_ISSUANCE" in signals:
        return True, "Multi-Purpose Token detected", ["MPT"]
    return False, "Not an MPT", []

STRATEGY_REGISTRY = {
    "trustline_spike_watch": trustline_spike_watch,
    "amm_seeded_launch_watch": amm_seeded_launch_watch,
    "metadata_backed_high_attention": metadata_backed_high_attention,
    "avoid_offer_only_noise": avoid_offer_only_noise,
    "early_but_validated_watch": early_but_validated_watch,
    "liquidity_first_watch": liquidity_first_watch,
    "conservative_metadata_only": conservative_metadata_only,
    "aggressive_high_attention_paper_only": aggressive_high_attention_paper_only,
    "clawback_risk_avoidance": clawback_risk_avoidance,
    "mpt_feature_watch": mpt_feature_watch
}
