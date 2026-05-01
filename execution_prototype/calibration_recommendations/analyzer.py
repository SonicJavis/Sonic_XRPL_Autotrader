import hashlib
from typing import List, Dict, Any
from execution_prototype.calibration_recommendations.models import CalibrationObservation

SCHEMA_VERSION = "1.0.0"

def _is_metadata_backed(record: Dict[str, Any]) -> bool:
    flags = record.get("drift_flags", [])
    if "MISSING_METADATA" in flags:
        return False
    if "INSUFFICIENT_REALITY_DATA" in flags:
        return False
    
    # If the actual delivered amount is explicitly present, it's metadata backed.
    # We must treat None, missing, empty strictly.
    if record.get("actual_delivered_amount") is not None:
        return True
    
    if record.get("actual_slippage") is not None:
        return True
        
    return False

def _determine_confidence(
    count: int, 
    meta_count: int, 
    drift_flag: str, 
    manual_count: int
) -> str:
    # "Never produce high confidence for..."
    if drift_flag in [
        "MISSING_METADATA", 
        "INSUFFICIENT_REALITY_DATA", 
        "TES_SUCCESS_BUT_OUTCOME_UNKNOWN",
        "MANUAL_STATUS_ONLY",
        "AMBIGUOUS_MATCH",
        "TX_NOT_VALIDATED"
    ]:
        if drift_flag == "TX_NOT_VALIDATED": # technically could be high if it's proven not validated on ledger, but prompt says "Never high without ledger confirmation." We don't have a reliable way to distinguish, so never high.
            pass
        elif drift_flag == "TES_SUCCESS_BUT_OUTCOME_UNKNOWN": # "Never high unless paired with validated metadata... which case flag likely not exist"
            pass
        return "low" if count < 3 else "medium"
        
    if count >= 10 and meta_count >= 10:
        return "high"
        
    if (3 <= count <= 9) or (count >= 10 and meta_count < count):
        return "medium"
        
    return "low"

def generate_observation_id(drift_flag: str, affected_records: List[str], report_hash: str) -> str:
    sorted_ids = sorted(affected_records)
    basis = f"{SCHEMA_VERSION}{drift_flag}{''.join(sorted_ids)}{report_hash}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def analyze_records(records: List[Dict[str, Any]], report_hash: str) -> List[CalibrationObservation]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    
    for r in records:
        flags = r.get("drift_flags", [])
        for f in flags:
            if f not in groups:
                groups[f] = []
            groups[f].append(r)
            
    observations = []
    
    for flag, flag_records in groups.items():
        affected_ids = [r.get("reconciliation_id", "") for r in flag_records]
        
        meta_count = sum(1 for r in flag_records if _is_metadata_backed(r))
        non_meta_count = len(flag_records) - meta_count
        manual_count = sum(1 for r in flag_records if "MANUAL_STATUS_ONLY" in r.get("drift_flags", []))
        
        confidence = _determine_confidence(len(flag_records), meta_count, flag, manual_count)
        
        obs_id = generate_observation_id(flag, affected_ids, report_hash)
        
        limits = []
        if non_meta_count > 0:
            limits.append("Partial or full lack of XRPL metadata evidence.")
            
        obs = CalibrationObservation(
            observation_id=obs_id,
            schema_version=SCHEMA_VERSION,
            drift_flag=flag,
            count=len(flag_records),
            affected_records=affected_ids,
            metadata_backed_count=meta_count,
            non_metadata_count=non_meta_count,
            confidence=confidence,
            evidence_summary=f"Found {len(flag_records)} instances of {flag} ({meta_count} metadata-backed).",
            limitations=limits,
            source_report_hash=report_hash
        )
        observations.append(obs)
        
    return observations
