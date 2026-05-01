import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple, List
from execution_prototype.reconciliation.models import SimulationRecord, LifecycleRecord, ReconciliationRecord

SCHEMA_VERSION = "1.0.0"

def generate_reconciliation_id(
    simulation_id: str,
    session_id: str,
    tx_hash: str,
    sim_hash: str,
    life_hash: str
) -> str:
    # sha256(schema_version + simulation_id + session_id + tx_hash + source hashes).hexdigest()[:16]
    basis = f"{SCHEMA_VERSION}{simulation_id}{session_id}{tx_hash}{sim_hash}{life_hash}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def reconcile(sim: SimulationRecord, life: LifecycleRecord) -> ReconciliationRecord:
    drift_flags = []
    limitations = []
    notes = []

    # 1. Matching Quality
    match_status = "EXACT"
    if sim.session_id and sim.session_id != life.session_id:
        match_status = "SESSION_MISMATCH"
    elif life.intent_id and sim.intent_id != life.intent_id:
        match_status = "INTENT_MISMATCH"
        
    if not life.tx_hash:
        drift_flags.append("MISSING_TX_HASH")
        limitations.append("Transaction hash is unknown.")

    # 2. Status Match
    expected_status = sim.expected_status
    actual_status = life.actual_status
    
    # We must treat actual_status interpreting tesSUCCESS
    # tesSUCCESS just means applied.
    status_match = expected_status == actual_status
    if not status_match:
        drift_flags.append("STATUS_MISMATCH")
        
    if life.actual_result_code == "tesSUCCESS" and not life.has_metadata:
        drift_flags.append("TES_SUCCESS_BUT_OUTCOME_UNKNOWN")
        limitations.append("tesSUCCESS applied but no metadata exists to confirm actual delivery/fill.")
        
    if not life.has_metadata:
        drift_flags.append("MISSING_METADATA")
        limitations.append("Missing XRPL metadata; cannot determine actual outcome")
        drift_flags.append("INSUFFICIENT_REALITY_DATA")
        
    if "manual" in actual_status.lower() or life.actual_status == "validated":
        drift_flags.append("MANUAL_STATUS_ONLY")
        
    if not life.actual_validated and not life.validated_at:
        drift_flags.append("TX_NOT_VALIDATED")
        if life.actual_status in ["submitted", "created", "signed"] or life.submitted_at:
            limitations.append("Transaction not confirmed within validation window")

    # 3. Fees
    fee_delta = None
    if sim.expected_fee_drops is not None and life.actual_fee_drops is not None:
        fee_delta = life.actual_fee_drops - sim.expected_fee_drops
        if fee_delta != 0:
            drift_flags.append("FEE_MISMATCH")
    
    # 4. Validation Ledger
    val_delta = None
    if sim.expected_validation_ledger is not None and life.actual_validation_ledger is not None:
        val_delta = life.actual_validation_ledger - sim.expected_validation_ledger
        if val_delta != 0:
            drift_flags.append("VALIDATION_LEDGER_MISMATCH")
            
    # 5. Fill Analysis
    fill_delta = None
    actual_delivered = None
    if life.has_metadata and life.actual_delivered_amount is not None:
        actual_delivered = life.actual_delivered_amount
        if sim.expected_fill_amount is not None:
            try:
                e_val = float(sim.expected_fill_amount)
                a_val = float(actual_delivered)
                fill_delta = a_val - e_val
                if abs(fill_delta) > 0.000001:
                    drift_flags.append("FILL_MISMATCH")
                    if fill_delta < 0:
                        drift_flags.append("LIQUIDITY_OVERESTIMATION")
            except ValueError:
                pass
    elif not life.has_metadata and sim.expected_fill_amount is not None:
        drift_flags.append("INSUFFICIENT_REALITY_DATA")
        
    # 6. Slippage Analysis
    slip_delta = None
    if sim.expected_slippage is not None and life.actual_slippage is not None:
        slip_delta = life.actual_slippage - sim.expected_slippage
        if abs(slip_delta) > 0.000001:
            drift_flags.append("SLIPPAGE_MISMATCH")
    
    # Deduplicate flags
    drift_flags = sorted(list(set(drift_flags)))
    limitations = sorted(list(set(limitations)))
    
    tx_hash = life.tx_hash or ""
    
    rec_id = generate_reconciliation_id(
        simulation_id=sim.simulation_id,
        session_id=life.session_id,
        tx_hash=tx_hash,
        sim_hash=sim.raw_hash,
        life_hash=life.raw_hash
    )
    
    compared_at = datetime.now(timezone.utc).isoformat()
    
    return ReconciliationRecord(
        reconciliation_id=rec_id,
        schema_version=SCHEMA_VERSION,
        simulation_id=sim.simulation_id,
        intent_id=sim.intent_id,
        session_id=life.session_id,
        tx_hash=life.tx_hash,
        compared_at=compared_at,
        match_status=match_status,
        expected_status=expected_status,
        actual_status=actual_status,
        status_match=status_match,
        fee_expected_drops=sim.expected_fee_drops,
        fee_actual_drops=life.actual_fee_drops,
        fee_delta_drops=fee_delta,
        validation_ledger_expected=sim.expected_validation_ledger,
        validation_ledger_actual=life.actual_validation_ledger,
        validation_ledger_delta=val_delta,
        expected_fill_amount=sim.expected_fill_amount,
        actual_delivered_amount=actual_delivered,
        fill_delta=fill_delta,
        expected_slippage=sim.expected_slippage,
        actual_slippage=life.actual_slippage, # Ensure models map this
        slippage_delta=slip_delta,
        drift_flags=drift_flags,
        limitations=limitations,
        notes=notes,
        source_simulation_hash=sim.raw_hash,
        source_lifecycle_hash=life.raw_hash
    )

def reconcile_ambiguous(sim: SimulationRecord) -> ReconciliationRecord:
    rec_id = generate_reconciliation_id(
        simulation_id=sim.simulation_id,
        session_id=sim.session_id or "",
        tx_hash="",
        sim_hash=sim.raw_hash,
        life_hash=""
    )
    return ReconciliationRecord(
        reconciliation_id=rec_id,
        schema_version=SCHEMA_VERSION,
        simulation_id=sim.simulation_id,
        intent_id=sim.intent_id,
        session_id=sim.session_id,
        tx_hash=None,
        compared_at=datetime.now(timezone.utc).isoformat(),
        match_status="insufficient_data",
        expected_status=sim.expected_status,
        actual_status="unknown",
        status_match=False,
        fee_expected_drops=sim.expected_fee_drops,
        fee_actual_drops=None,
        fee_delta_drops=None,
        validation_ledger_expected=sim.expected_validation_ledger,
        validation_ledger_actual=None,
        validation_ledger_delta=None,
        expected_fill_amount=sim.expected_fill_amount,
        actual_delivered_amount=None,
        fill_delta=None,
        expected_slippage=sim.expected_slippage,
        actual_slippage=None,
        slippage_delta=None,
        drift_flags=["AMBIGUOUS_MATCH"],
        limitations=["Multiple candidates matched; reconciliation aborted to preserve determinism"],
        notes=[],
        source_simulation_hash=sim.raw_hash,
        source_lifecycle_hash=""
    )
