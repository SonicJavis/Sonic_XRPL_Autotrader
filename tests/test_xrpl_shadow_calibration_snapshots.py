import json
from datetime import datetime, timezone

from app.calibration.xrpl_bayesian_calibrator import build_xrpl_shadow_calibration_aggregate
from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot


def _aggregate_snapshot_data():
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    executions = [
        ExecutionRecord(
            id=1,
            token_id=1,
            signal_id=1,
            snapshot_id=1,
            side="BUY",
            requested_size=100.0,
            filled_size=70.0,
            fill_status="PARTIAL",
            avg_fill_price=1.03,
            snapshot_time=now,
            signal_time=now,
            execution_time=now,
            ledger_index_snapshot=100,
            ledger_index_signal=100,
            ledger_index_execution=102,
            ledger_index_inclusion=102,
            execution_details_json=json.dumps(
                {
                    "shadow": True,
                    "observed_fill_ratio": 0.15,
                    "observed_possible_fill": 15.0,
                    "path_execution_risk": 0.6,
                    "route_confidence": 0.25,
                    "observation_confidence": 0.7,
                    "ledger_delay_error": 0.3,
                    "routes_seen": ["direct", "auto_bridge"],
                }
            ),
        )
    ]
    snapshots = [
        XRPLOrderbookSnapshot(
            token_id=1,
            ledger_index=100,
            best_bid=0.99,
            best_ask=1.01,
            bid_depth_xrp=300.0,
            ask_depth_xrp=280.0,
            spread_pct=2.0,
            observed_at=now,
        ),
        XRPLOrderbookSnapshot(
            token_id=1,
            ledger_index=102,
            best_bid=0.98,
            best_ask=1.03,
            bid_depth_xrp=210.0,
            ask_depth_xrp=160.0,
            spread_pct=3.0,
            observed_at=now,
        ),
    ]
    return build_xrpl_shadow_calibration_aggregate(
        executions=executions,
        orderbook_snapshots=snapshots,
    )


def test_xrpl_shadow_calibration_error_snapshot() -> None:
    aggregate = _aggregate_snapshot_data()
    payload = {
        "sample_count": aggregate.sample_count,
        "shadow_disagreement_avg": aggregate.shadow_disagreement_avg,
        "phantom_liquidity_avg": aggregate.phantom_liquidity_avg,
        "phantom_penalty_avg": aggregate.phantom_penalty_avg,
        "route_instability_avg": aggregate.route_instability_avg,
        "competition_failure_rate": aggregate.competition_failure_rate,
        "fill_variance_avg": aggregate.fill_variance_avg,
        "low_fill_bias_avg": aggregate.low_fill_bias_avg,
        "price_error_norm_avg": aggregate.price_error_norm_avg,
        "liquidity_error_avg": aggregate.liquidity_error_avg,
        "ledger_delay_error_avg": aggregate.ledger_delay_error_avg,
        "path_error_avg": aggregate.path_error_avg,
        "observation_confidence_avg": aggregate.observation_confidence_avg,
        "snapshot_derived_liquidity_avg": aggregate.snapshot_derived_liquidity_avg,
        "observed_possible_fill_avg": aggregate.observed_possible_fill_avg,
    }
    assert payload == {
        "sample_count": 1,
        "shadow_disagreement_avg": 0.7865,
        "phantom_liquidity_avg": 265.0,
        "phantom_penalty_avg": 1.0,
        "route_instability_avg": 1.0,
        "competition_failure_rate": 1.0,
        "fill_variance_avg": 0.55,
        "low_fill_bias_avg": 0.55,
        "price_error_norm_avg": 0.0,
        "liquidity_error_avg": 0.85,
        "ledger_delay_error_avg": 0.3,
        "path_error_avg": 0.6,
        "observation_confidence_avg": 0.7,
        "snapshot_derived_liquidity_avg": 280.0,
        "observed_possible_fill_avg": 15.0,
    }


def test_xrpl_shadow_calibration_reliability_snapshot() -> None:
    calibration = _aggregate_snapshot_data().calibration
    payload = {
        "liquidity_reliability": calibration.liquidity_reliability.lower_bound,
        "path_reliability": calibration.path_reliability.lower_bound,
        "latency_reliability": calibration.latency_reliability.lower_bound,
        "fill_reliability": calibration.fill_reliability.lower_bound,
        "competition_reliability": calibration.competition_reliability.lower_bound,
    }
    assert payload == {
        "liquidity_reliability": 0.0,
        "path_reliability": 0.0,
        "latency_reliability": 0.222958,
        "fill_reliability": 0.328249,
        "competition_reliability": 0.0,
    }


def test_xrpl_shadow_calibration_recommendation_snapshot() -> None:
    recommendations = _aggregate_snapshot_data().calibration.recommendations
    payload = {
        "liquidity_haircut": recommendations.liquidity_haircut,
        "expected_slippage_multiplier": recommendations.expected_slippage_multiplier,
        "execution_probability_floor": recommendations.execution_probability_floor,
        "competition_risk_multiplier": recommendations.competition_risk_multiplier,
    }
    assert payload == {
        "liquidity_haircut": 1.0,
        "expected_slippage_multiplier": 2.0,
        "execution_probability_floor": 0.328249,
        "competition_risk_multiplier": 2.0,
    }