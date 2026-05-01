import pytest
from execution_prototype.calibration_recommendations.analyzer import analyze_records, generate_observation_id
from execution_prototype.calibration_recommendations.recommendation_engine import generate_recommendations, generate_recommendation_id

def test_deterministic_ids():
    obs_id1 = generate_observation_id("FEE_MISMATCH", ["rec1", "rec2"], "hash1")
    obs_id2 = generate_observation_id("FEE_MISMATCH", ["rec2", "rec1"], "hash1")
    assert obs_id1 == obs_id2
    
    rec_id1 = generate_recommendation_id("fee_model", "Review", ["rec1", "rec2"], "hash1")
    rec_id2 = generate_recommendation_id("fee_model", "Review", ["rec2", "rec1"], "hash1")
    assert rec_id1 == rec_id2

def test_fee_mismatch_creates_fee_model_review():
    records = [{"reconciliation_id": "1", "drift_flags": ["FEE_MISMATCH"], "actual_delivered_amount": "100"}]
    obs = analyze_records(records, "hash")
    assert len(obs) == 1
    recs = generate_recommendations(obs)
    assert len(recs) == 1
    assert recs[0].category == "fee_model"
    assert "fee estimates" in recs[0].prohibited_auto_action

def test_tes_success_but_outcome_unknown_never_infers_success():
    records = [{"reconciliation_id": "1", "drift_flags": ["TES_SUCCESS_BUT_OUTCOME_UNKNOWN"]}]
    obs = analyze_records(records, "hash")
    recs = generate_recommendations(obs)
    assert recs[0].category == "metadata_collection"
    assert "tesSUCCESS" in recs[0].prohibited_auto_action
    assert obs[0].confidence == "low"

def test_missing_metadata_creates_metadata_collection():
    records = [{"reconciliation_id": "1", "drift_flags": ["MISSING_METADATA"]}]
    obs = analyze_records(records, "hash")
    recs = generate_recommendations(obs)
    assert recs[0].category == "metadata_collection"
    assert obs[0].confidence == "low"

def test_insufficient_reality_data_never_high_confidence():
    records = [{"reconciliation_id": str(i), "drift_flags": ["INSUFFICIENT_REALITY_DATA"]} for i in range(15)]
    obs = analyze_records(records, "hash")
    assert obs[0].confidence == "medium" # count > 3 but still never high
    assert obs[0].metadata_backed_count == 0

def test_ambiguous_match_never_selects():
    records = [{"reconciliation_id": "1", "drift_flags": ["AMBIGUOUS_MATCH"]}]
    obs = analyze_records(records, "hash")
    recs = generate_recommendations(obs)
    assert recs[0].category == "matching_quality"
    assert "Do not select first/best/nearest match" in recs[0].prohibited_auto_action

def test_tx_not_validated_creates_validation_process():
    records = [{"reconciliation_id": "1", "drift_flags": ["TX_NOT_VALIDATED"]}]
    obs = analyze_records(records, "hash")
    recs = generate_recommendations(obs)
    assert recs[0].category == "validation_process"
    assert "unvalidated" in recs[0].prohibited_auto_action

def test_fill_mismatch_without_metadata_downgrades():
    records = [{"reconciliation_id": "1", "drift_flags": ["FILL_MISMATCH"]}]
    obs = analyze_records(records, "hash")
    recs = generate_recommendations(obs)
    assert recs[0].category == "metadata_collection" # downgraded

def test_slippage_mismatch_without_metadata_ignores():
    records = [{"reconciliation_id": "1", "drift_flags": ["SLIPPAGE_MISMATCH"]}]
    obs = analyze_records(records, "hash")
    recs = generate_recommendations(obs)
    assert len(recs) == 0 # skipped if no metadata

def test_high_confidence_requires_metadata():
    records = [{"reconciliation_id": str(i), "drift_flags": ["FEE_MISMATCH"], "actual_delivered_amount": "10"} for i in range(10)]
    obs = analyze_records(records, "hash")
    assert obs[0].confidence == "high"

def test_append_only_and_no_source_mod(tmp_path):
    from execution_prototype.calibration_recommendations.report_writer import write_reports
    from execution_prototype.calibration_recommendations.models import CalibrationSummary
    
    records = [{"reconciliation_id": "1", "drift_flags": ["FEE_MISMATCH"]}]
    obs = analyze_records(records, "hash")
    recs = generate_recommendations(obs)
    sum_obj = CalibrationSummary("1.0", "now", "path", "hash", 1, 1, {}, {}, {}, [], "safe")
    
    out1 = write_reports(obs, recs, sum_obj, str(tmp_path))
    assert len(out1["files"]) == 4
    
    import time
    time.sleep(1.1)
    out2 = write_reports(obs, recs, sum_obj, str(tmp_path))
    assert out1["files"] != out2["files"] # new timestamp dir
