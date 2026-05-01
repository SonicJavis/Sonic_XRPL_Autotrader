from typing import List, Dict, Any
from execution_prototype.drift_intelligence.models import ConfidenceDecay

def _calculate_accuracy(records: List[Dict[str, Any]], flag_name: str) -> float:
    if not records:
        return 1.0
    errors = sum(1 for r in records if flag_name in r.get("drift_flags", []))
    return 1.0 - (errors / len(records))

def calculate_confidence_decay(runs: List[Dict[str, Any]]) -> List[ConfidenceDecay]:
    if len(runs) < 2:
        return []
        
    first_run_records = runs[0].get("reconciliation_records", [])
    last_run_records = runs[-1].get("reconciliation_records", [])
    
    metrics_to_track = {
        "fill_accuracy": "FILL_MISMATCH",
        "slippage_accuracy": "SLIPPAGE_MISMATCH",
        "validation_accuracy": "TX_NOT_VALIDATED",
        "metadata_completeness": "MISSING_METADATA"
    }
    
    decays = []
    
    for metric_name, flag in metrics_to_track.items():
        prev_acc = _calculate_accuracy(first_run_records, flag)
        curr_acc = _calculate_accuracy(last_run_records, flag)
        
        decay_rate = prev_acc - curr_acc
        is_decaying = decay_rate > 0.05
        
        # Missing metadata forces metadata dependency checks
        meta_missing_ratio = 1.0 - _calculate_accuracy(last_run_records, "MISSING_METADATA")
        metadata_dependency = meta_missing_ratio > 0.1
        
        decays.append(ConfidenceDecay(
            metric=metric_name,
            previous_value=prev_acc,
            current_value=curr_acc,
            decay_rate=decay_rate,
            decay_flag=is_decaying,
            metadata_dependency=metadata_dependency
        ))
        
    return decays
