from app.calibration.xrpl_bayesian_calibrator import (
    XRPLBayesianCalibrationSummary,
    XRPLReliabilityDimension,
    XRPLShadowCalibrationAggregate,
    XRPLShadowRecommendations,
)
from app.decision.xrpl_trade_gate import XRPLTradeGate, XRPLTradeGateInput


def _dimension(lower_bound: float) -> XRPLReliabilityDimension:
    return XRPLReliabilityDimension(
        lower_bound=lower_bound,
        mean=lower_bound,
        std=0.0,
        alpha=1.0,
        beta=1.0,
        adaptive_weight=1.0,
    )


def _aggregate(
    *,
    liquidity_haircut: float,
    expected_slippage_multiplier: float,
    execution_probability_floor: float,
    competition_risk_multiplier: float = 1.0,
    phantom_penalty_avg: float,
    route_instability_avg: float,
    competition_failure_rate: float,
) -> XRPLShadowCalibrationAggregate:
    return XRPLShadowCalibrationAggregate(
        sample_count=1,
        shadow_disagreement_avg=0.5,
        phantom_liquidity_avg=10.0,
        phantom_penalty_avg=phantom_penalty_avg,
        route_instability_avg=route_instability_avg,
        competition_failure_rate=competition_failure_rate,
        fill_variance_avg=0.2,
        low_fill_bias_avg=0.2,
        price_error_norm_avg=0.1,
        liquidity_error_avg=0.2,
        ledger_delay_error_avg=0.2,
        path_error_avg=0.2,
        observation_confidence_avg=0.7,
        snapshot_derived_liquidity_avg=50.0,
        observed_possible_fill_avg=30.0,
        calibration=XRPLBayesianCalibrationSummary(
            sample_count=1,
            decay_half_life=300.0,
            liquidity_reliability=_dimension(1.0 - liquidity_haircut),
            path_reliability=_dimension(1.0 - route_instability_avg),
            latency_reliability=_dimension(0.7),
            fill_reliability=_dimension(execution_probability_floor),
            competition_reliability=_dimension(max(0.0, 1.0 - (competition_risk_multiplier - 1.0))),
            drift_reliability=_dimension(0.7),
            latency_stability=_dimension(0.7),
            path_reliability_weighting=_dimension(max(0.0, 1.0 - route_instability_avg)),
            recommendations=XRPLShadowRecommendations(
                liquidity_haircut=liquidity_haircut,
                expected_slippage_multiplier=expected_slippage_multiplier,
                execution_probability_floor=execution_probability_floor,
                competition_risk_multiplier=competition_risk_multiplier,
            ),
            phantom_penalty_avg=phantom_penalty_avg,
            weighted_error_avg=0.5,
        ),
        samples=[],
    )


def test_phantom_liquidity_reduces_effective_size() -> None:
    gate = XRPLTradeGate()
    low = gate.evaluate(
        XRPLTradeGateInput(
            requested_size=100.0,
            expected_profit=20.0,
            expected_loss=10.0,
            threshold=0.0,
            execution_probability_floor=0.8,
            slippage_multiplier=1.0,
            liquidity_haircut=0.1,
            phantom_penalty=0.1,
            route_instability=0.0,
            competition_penalty=0.0,
        )
    )
    high = gate.evaluate(
        XRPLTradeGateInput(
            requested_size=100.0,
            expected_profit=20.0,
            expected_loss=10.0,
            threshold=0.0,
            execution_probability_floor=0.8,
            slippage_multiplier=1.0,
            liquidity_haircut=0.1,
            phantom_penalty=0.5,
            route_instability=0.0,
            competition_penalty=0.0,
        )
    )

    assert high.effective_size < low.effective_size


def test_route_instability_reduces_execution_probability() -> None:
    gate = XRPLTradeGate()
    stable = gate.evaluate(
        XRPLTradeGateInput(
            requested_size=100.0,
            expected_profit=10.0,
            expected_loss=5.0,
            threshold=0.0,
            execution_probability_floor=0.7,
            slippage_multiplier=1.0,
            liquidity_haircut=0.1,
            phantom_penalty=0.1,
            route_instability=0.1,
            competition_penalty=0.0,
        )
    )
    unstable = gate.evaluate(
        XRPLTradeGateInput(
            requested_size=100.0,
            expected_profit=10.0,
            expected_loss=5.0,
            threshold=0.0,
            execution_probability_floor=0.7,
            slippage_multiplier=1.0,
            liquidity_haircut=0.1,
            phantom_penalty=0.1,
            route_instability=0.6,
            competition_penalty=0.0,
        )
    )

    assert unstable.latency_path_adjusted_probability < stable.latency_path_adjusted_probability
    assert "ROUTE_UNSTABLE" in unstable.risk_flags


def test_competition_penalty_blocks_trade() -> None:
    gate = XRPLTradeGate()
    decision = gate.evaluate(
        XRPLTradeGateInput(
            requested_size=100.0,
            expected_profit=12.0,
            expected_loss=6.0,
            threshold=0.0,
            execution_probability_floor=0.6,
            slippage_multiplier=1.0,
            liquidity_haircut=0.1,
            phantom_penalty=0.1,
            route_instability=0.1,
            competition_penalty=1.0,
        )
    )

    assert decision.allow_trade is False
    assert decision.latency_path_adjusted_probability == 0.0
    assert "COMPETITION_RISK_HIGH" in decision.risk_flags


def test_high_slippage_reduces_uncertainty_adjusted_value() -> None:
    gate = XRPLTradeGate()
    low = gate.evaluate(
        XRPLTradeGateInput(
            requested_size=100.0,
            expected_profit=20.0,
            expected_loss=5.0,
            threshold=0.0,
            execution_probability_floor=0.8,
            slippage_multiplier=1.0,
            liquidity_haircut=0.1,
            phantom_penalty=0.1,
            route_instability=0.1,
            competition_penalty=0.0,
        )
    )
    high = gate.evaluate(
        XRPLTradeGateInput(
            requested_size=100.0,
            expected_profit=20.0,
            expected_loss=5.0,
            threshold=0.0,
            execution_probability_floor=0.8,
            slippage_multiplier=2.0,
            liquidity_haircut=0.1,
            phantom_penalty=0.1,
            route_instability=0.1,
            competition_penalty=0.0,
        )
    )

    assert high.uncertainty_adjusted_value < low.uncertainty_adjusted_value
    assert "HIGH_SLIPPAGE_ENVIRONMENT" in high.risk_flags


def test_low_reliability_blocks_trade() -> None:
    gate = XRPLTradeGate()
    decision = gate.evaluate_shadow_calibration(
        calibration=_aggregate(
            liquidity_haircut=0.8,
            expected_slippage_multiplier=1.8,
            execution_probability_floor=0.1,
            competition_risk_multiplier=1.8,
            phantom_penalty_avg=0.5,
            route_instability_avg=0.7,
            competition_failure_rate=0.6,
        ),
        requested_size=100.0,
        expected_profit=15.0,
        expected_loss=10.0,
        threshold=0.0,
    )

    assert decision.allow_trade is False
    assert "LOW_EXECUTION_PROBABILITY" in decision.risk_flags


def test_trade_gate_outputs_are_deterministic() -> None:
    gate = XRPLTradeGate()
    data = XRPLTradeGateInput(
        requested_size=75.0,
        expected_profit=9.0,
        expected_loss=4.0,
        threshold=0.5,
        execution_probability_floor=0.55,
        slippage_multiplier=1.25,
        liquidity_haircut=0.2,
        phantom_penalty=0.15,
        route_instability=0.25,
        competition_penalty=0.1,
    )

    first = gate.evaluate(data)
    second = gate.evaluate(data)

    assert first == second
