import hashlib
from typing import List, Dict, Any
from execution_prototype.drift_intelligence.models import ReplayRecord

def generate_replay_hash(record: Dict[str, Any]) -> str:
    # Hash the core deterministic outputs of a reconciliation record to ensure stability
    keys_to_hash = [
        "reconciliation_id",
        "session_id",
        "intent_id",
        "drift_flags",
        "actual_delivered_amount",
        "actual_slippage"
    ]
    
    parts = []
    for k in keys_to_hash:
        val = record.get(k)
        if isinstance(val, list):
            parts.append(f"{k}:{','.join(sorted(val))}")
        else:
            parts.append(f"{k}:{val}")
            
    basis = "|".join(parts)
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()

def validate_replay(runs: List[Dict[str, Any]]) -> List[ReplayRecord]:
    # Check consistency of identical reconciliation_ids across multiple runs
    seen_records: Dict[str, Dict[str, Any]] = {}
    seen_hashes: Dict[str, str] = {}
    
    replay_results = []
    
    for run in runs:
        for rec in run.get("reconciliation_records", []):
            rec_id = rec.get("reconciliation_id")
            if not rec_id:
                continue
                
            current_hash = generate_replay_hash(rec)
            
            if rec_id in seen_hashes:
                prev_hash = seen_hashes[rec_id]
                match = (prev_hash == current_hash)
                
                dev_type = "none" if match else "non_deterministic_output"
                notes = []
                
                if not match:
                    prev_rec = seen_records[rec_id]
                    prev_flags = set(prev_rec.get("drift_flags", []))
                    curr_flags = set(rec.get("drift_flags", []))
                    
                    if "MISSING_METADATA" in prev_flags ^ curr_flags:
                        dev_type = "metadata_dependency_shift"
                        notes.append("Metadata presence changed between replays.")
                    else:
                        notes.append(f"Hash mismatch: {prev_hash} vs {current_hash}")
                        
                replay_results.append(ReplayRecord(
                    reconciliation_id=rec_id,
                    replay_hash=current_hash,
                    deterministic_match=match,
                    deviation_type=dev_type,
                    notes=notes
                ))
            else:
                seen_hashes[rec_id] = current_hash
                seen_records[rec_id] = rec
                
    return replay_results
