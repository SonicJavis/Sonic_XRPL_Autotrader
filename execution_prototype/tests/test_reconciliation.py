import pytest
from pathlib import Path
from execution_prototype.reconciliation.models import SimulationRecord, LifecycleRecord, ReconciliationRecord
from execution_prototype.reconciliation.comparator import reconcile, generate_reconciliation_id, reconcile_ambiguous
from execution_prototype.reconciliation.report_writer import write_reports

def test_deterministic_ids():
    id1 = generate_reconciliation_id("sim1", "ses1", "hash1", "simh", "lifeh")
    id2 = generate_reconciliation_id("sim1", "ses1", "hash1", "simh", "lifeh")
    id3 = generate_reconciliation_id("sim2", "ses1", "hash1", "simh", "lifeh")
    assert id1 == id2
    assert id1 != id3
    assert len(id1) == 16

def test_missing_metadata_handling():
    sim = SimulationRecord(
        simulation_id="sim1", intent_id="int1", expected_tx_type="Payment",
        expected_status="validated", source_path="p", raw_hash="h",
        created_at="t", session_id="ses1", expected_fill_amount="100.0"
    )
    life = LifecycleRecord(
        session_id="ses1", actual_status="validated", source_path="p", raw_hash="h",
        actual_result_code="tesSUCCESS", actual_delivered_amount=None, has_metadata=False, tx_hash="tx1",
        actual_validated=True
    )
    rec = reconcile(sim, life)
    assert "MISSING_METADATA" in rec.drift_flags
    assert "INSUFFICIENT_REALITY_DATA" in rec.drift_flags
    assert "TES_SUCCESS_BUT_OUTCOME_UNKNOWN" in rec.drift_flags
    assert rec.actual_delivered_amount is None
    assert rec.fill_delta is None

def test_no_inference_when_data_missing():
    sim = SimulationRecord(
        simulation_id="sim1", intent_id="int1", expected_tx_type="Payment",
        expected_status="validated", source_path="p", raw_hash="h",
        created_at="t", session_id="ses1", expected_slippage=0.01
    )
    life = LifecycleRecord(
        session_id="ses1", actual_status="validated", source_path="p", raw_hash="h",
        actual_slippage=None, has_metadata=True, tx_hash="tx1", actual_validated=True
    )
    rec = reconcile(sim, life)
    assert rec.slippage_delta is None
    assert "SLIPPAGE_MISMATCH" not in rec.drift_flags

def test_ambiguous_match():
    sim = SimulationRecord(
        simulation_id="sim1", intent_id="int1", expected_tx_type="Payment",
        expected_status="validated", source_path="p", raw_hash="h",
        created_at="t", session_id="ses1"
    )
    # The new logic generates ambiguous via reconcile_ambiguous
    rec = reconcile_ambiguous(sim)
    assert rec.match_status == "insufficient_data"
    assert "AMBIGUOUS_MATCH" in rec.drift_flags
    assert rec.tx_hash is None
    assert rec.actual_delivered_amount is None
    assert rec.fill_delta is None

def test_unvalidated_tx():
    sim = SimulationRecord(
        simulation_id="sim1", intent_id="int1", expected_tx_type="Payment",
        expected_status="validated", source_path="p", raw_hash="h", created_at="t"
    )
    life = LifecycleRecord(
        session_id="ses1", actual_status="submitted", source_path="p", raw_hash="h", tx_hash="tx1",
        actual_validated=False, submitted_at="t2", has_metadata=True
    )
    rec = reconcile(sim, life)
    assert "TX_NOT_VALIDATED" in rec.drift_flags
    assert any("not confirmed within validation window" in lim for lim in rec.limitations)

def test_append_only_guarantee_and_no_source_mod(tmp_path):
    sim = SimulationRecord(
        simulation_id="sim1", intent_id="int1", expected_tx_type="Payment",
        expected_status="validated", source_path="p", raw_hash="h", created_at="t"
    )
    life = LifecycleRecord(
        session_id="ses1", actual_status="validated", source_path="p", raw_hash="h", tx_hash="tx1", actual_validated=True
    )
    rec = reconcile(sim, life)
    
    # Run once
    out1 = write_reports([rec], str(tmp_path))
    folder1 = Path(out1["files"][0]).parent
    assert folder1.exists()
    
    # Run twice
    import time
    time.sleep(1.1)  # Ensure different timestamp
    out2 = write_reports([rec], str(tmp_path))
    folder2 = Path(out2["files"][0]).parent
    assert folder2.exists()
    assert folder1 != folder2
    
    # The simulation and lifecycle records are frozen dataclasses, preventing modification
    with pytest.raises(Exception):
        sim.simulation_id = "modified"
