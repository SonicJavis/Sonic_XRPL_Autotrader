import json
import hashlib
from pathlib import Path
from typing import List
from execution_prototype.reconciliation.models import SimulationRecord, LifecycleRecord

def calculate_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_simulations(source_dir: str) -> List[SimulationRecord]:
    records = []
    path = Path(source_dir)
    if not path.exists():
        return records
        
    for file_path in path.rglob("*.jsonl"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    raw_hash = calculate_hash(line)
                    
                    record = SimulationRecord(
                        simulation_id=data.get("simulation_id", f"sim_{raw_hash[:8]}"),
                        intent_id=data.get("intent_id", ""),
                        expected_tx_type=data.get("expected_tx_type", "unknown"),
                        expected_status=data.get("expected_status", "unknown"),
                        source_path=str(file_path),
                        raw_hash=raw_hash,
                        created_at=data.get("created_at", ""),
                        session_id=data.get("session_id"),
                        expected_fee_drops=data.get("expected_fee_drops"),
                        expected_validation_ledger=data.get("expected_validation_ledger"),
                        expected_fill_amount=str(data["expected_fill_amount"]) if "expected_fill_amount" in data else None,
                        expected_fill_pct=data.get("expected_fill_pct"),
                        expected_avg_price=data.get("expected_avg_price"),
                        expected_slippage=data.get("expected_slippage")
                    )
                    records.append(record)
                except Exception:
                    pass
    return records

def load_lifecycle_events(source_dir: str) -> List[LifecycleRecord]:
    # In payload_sessions.jsonl, each line is an event. We want to reconstruct the final state of each session.
    # Alternatively, the prompt implies reading from execution_prototype/data which might contain payload_sessions.jsonl or lifecycle_audit_log.jsonl
    records_map = {}
    path = Path(source_dir)
    if not path.exists():
        return []
        
    # Read payload_sessions.jsonl or similar
    for file_path in path.rglob("*.jsonl"):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    raw_hash = calculate_hash(line)
                    
                    # Depending on if it's the raw session object or an event wrapper
                    session_data = data.get("session", data)
                    session_id = session_data.get("session_id") or data.get("session_id")
                    
                    if not session_id:
                        continue
                        
                    xrpl_state = session_data.get("xrpl_state", {})
                    
                    has_metadata = "meta" in xrpl_state or "engine_result" in xrpl_state # Simplified assumption based on prototype
                    # For real outcome, we'd need delivered_amount from meta
                    actual_delivered = xrpl_state.get("meta", {}).get("delivered_amount")
                    
                    # Update mapping with latest event for this session
                    records_map[session_id] = LifecycleRecord(
                        session_id=session_id,
                        actual_status=session_data.get("status", data.get("status", "unknown")),
                        source_path=str(file_path),
                        raw_hash=raw_hash,
                        intent_id=session_data.get("intent_id", data.get("intent_id")),
                        payload_uuid=session_data.get("xaman_payload", {}).get("uuid"),
                        tx_hash=session_data.get("tx_hash", data.get("tx_hash")),
                        created_at=session_data.get("created_at"),
                        signed_at=None, # Extract if available
                        submitted_at=None,
                        validated_at=None,
                        actual_fee_drops=None, # Extract from meta if available
                        actual_validation_ledger=xrpl_state.get("ledger_index"),
                        actual_result_code=xrpl_state.get("engine_result"),
                        actual_validated=xrpl_state.get("validated", False),
                        actual_delivered_amount=actual_delivered,
                        actual_slippage=None,
                        has_metadata=has_metadata
                    )
                except Exception:
                    pass
                    
    return list(records_map.values())
