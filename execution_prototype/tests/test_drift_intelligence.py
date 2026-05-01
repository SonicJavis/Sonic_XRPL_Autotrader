import pytest
from execution_prototype.drift_intelligence.trend_analyzer import analyze_trends, calculate_slope
from execution_prototype.drift_intelligence.confidence_engine import calculate_confidence_decay
from execution_prototype.drift_intelligence.replay_validator import validate_replay, generate_replay_hash
from execution_prototype.drift_intelligence.early_warning import detect_early_warnings

def test_deterministic_slope():
    rates1 = [0.1, 0.2, 0.3]
    assert calculate_slope(rates1) > 0.05
    rates2 = [0.3, 0.2, 0.1]
    assert calculate_slope(rates2) < -0.05
    rates3 = [0.1, 0.1, 0.1]
    assert calculate_slope(rates3) == 0.0

def test_no_trend_with_few_runs():
    runs = [
        {"reconciliation_records": [{"drift_flags": ["FEE_MISMATCH"]}]},
        {"reconciliation_records": [{"drift_flags": ["FEE_MISMATCH"]}]}
    ]
    trends = analyze_trends(runs)
    fee_trend = next(t for t in trends if t.drift_flag == "FEE_MISMATCH")
    assert fee_trend.trend_direction == "INSUFFICIENT_TREND_DATA"
    assert fee_trend.confidence == "low"

def test_normalization_correctness():
    runs = [
        {"reconciliation_records": [{"drift_flags": ["FEE_MISMATCH"]}, {"drift_flags": []}]},
        {"reconciliation_records": [{"drift_flags": ["FEE_MISMATCH"]} for _ in range(5)] + [{"drift_flags": []} for _ in range(5)]},
        {"reconciliation_records": [{"drift_flags": ["FEE_MISMATCH"]} for _ in range(10)] + [{"drift_flags": []} for _ in range(10)]}
    ]
    trends = analyze_trends(runs)
    fee_trend = next(t for t in trends if t.drift_flag == "FEE_MISMATCH")
    # 1/2 = 0.5, 5/10 = 0.5, 10/20 = 0.5
    assert fee_trend.normalized_rate_per_run == [0.5, 0.5, 0.5]
    assert fee_trend.trend_direction == "stable"

def test_confidence_decay_rules():
    runs = [
        {"reconciliation_records": [{"drift_flags": []}]},
        {"reconciliation_records": [{"drift_flags": ["FILL_MISMATCH"]}]}
    ]
    decays = calculate_confidence_decay(runs)
    fill_decay = next(d for d in decays if d.metric == "fill_accuracy")
    assert fill_decay.previous_value == 1.0
    assert fill_decay.current_value == 0.0
    assert fill_decay.decay_flag is True

def test_replay_consistency():
    rec1 = {"reconciliation_id": "r1", "drift_flags": ["FEE_MISMATCH"]}
    rec2 = {"reconciliation_id": "r1", "drift_flags": ["FEE_MISMATCH"]}
    rec3 = {"reconciliation_id": "r1", "drift_flags": ["FEE_MISMATCH", "MISSING_METADATA"]}
    
    runs = [
        {"reconciliation_records": [rec1]},
        {"reconciliation_records": [rec2]},
        {"reconciliation_records": [rec3]}
    ]
    
    replays = validate_replay(runs)
    assert len(replays) == 2
    # run2 vs run1
    assert replays[0].deterministic_match is True
    # run3 vs run1/2
    assert replays[1].deterministic_match is False
    assert replays[1].deviation_type == "metadata_dependency_shift"

def test_early_warning_triggers():
    runs = [
        {"reconciliation_records": [{"drift_flags": []} for _ in range(10)]},
        {"reconciliation_records": [{"drift_flags": ["MISSING_METADATA"]} for _ in range(10)]},
        {"reconciliation_records": [{"drift_flags": ["MISSING_METADATA"]} for _ in range(20)]}
    ]
    trends = analyze_trends(runs)
    decays = calculate_confidence_decay(runs)
    warnings = detect_early_warnings(trends, decays)
    
    meta_warn = next((w for w in warnings if w.type == "metadata_collapse"), None)
    assert meta_warn is not None
    assert meta_warn.severity == "critical"
    assert "metadata" in meta_warn.description.lower()
