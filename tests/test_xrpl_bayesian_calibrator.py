from datetime import datetime, timedelta, timezone

from app.calibration.xrpl_bayesian_calibrator import (
    XRPLBayesianCalibrator,
    XRPLBayesianObservation,
)


def _observation(
    *,
    observed_at: datetime,
    liquidity_error: float,
    path_error: float,
    ledger_delay_error: float,
    fill_disagreement: float,
    low_fill_bias: float,
    competition_penalty: float,
    phantom_penalty: float = 0.0,
    route_instability: float = 0.0,
    sample_weight: float = 1.0,
    weighted_error: float = 0.5,
) -> XRPLBayesianObservation:
    return XRPLBayesianObservation(
        observed_at=observed_at,
        sample_weight=sample_weight,
        phantom_penalty=phantom_penalty,
        route_instability=route_instability,
        competition_penalty=competition_penalty,
        fill_disagreement=fill_disagreement,
        low_fill_bias=low_fill_bias,
        liquidity_error=liquidity_error,
        path_error=path_error,
        ledger_delay_error=ledger_delay_error,
        weighted_error=weighted_error,
    )


def test_bayesian_calibrator_applies_time_decay_to_old_failures() -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    calibrator = XRPLBayesianCalibrator(decay_half_life=300.0)

    decayed = calibrator.calibrate(
        [
            _observation(
                observed_at=now - timedelta(seconds=900),
                liquidity_error=0.0,
                path_error=0.0,
                ledger_delay_error=0.0,
                fill_disagreement=1.0,
                low_fill_bias=1.0,
                competition_penalty=1.0,
            ),
            _observation(
                observed_at=now,
                liquidity_error=0.0,
                path_error=0.0,
                ledger_delay_error=0.0,
                fill_disagreement=0.0,
                low_fill_bias=0.0,
                competition_penalty=0.0,
            ),
        ],
        as_of=now,
    )
    non_decayed = calibrator.calibrate(
        [
            _observation(
                observed_at=now,
                liquidity_error=0.0,
                path_error=0.0,
                ledger_delay_error=0.0,
                fill_disagreement=1.0,
                low_fill_bias=1.0,
                competition_penalty=1.0,
            ),
            _observation(
                observed_at=now,
                liquidity_error=0.0,
                path_error=0.0,
                ledger_delay_error=0.0,
                fill_disagreement=0.0,
                low_fill_bias=0.0,
                competition_penalty=0.0,
            ),
        ],
        as_of=now,
    )

    assert decayed.fill_reliability.lower_bound > non_decayed.fill_reliability.lower_bound
    assert decayed.competition_reliability.lower_bound > non_decayed.competition_reliability.lower_bound


def test_bayesian_calibrator_recommendations_use_lower_bounds_only() -> None:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    summary = XRPLBayesianCalibrator(decay_half_life=300.0).calibrate(
        [
            _observation(
                observed_at=now,
                liquidity_error=0.6,
                path_error=0.5,
                ledger_delay_error=0.4,
                fill_disagreement=0.7,
                low_fill_bias=0.6,
                competition_penalty=0.8,
                phantom_penalty=0.5,
                route_instability=0.4,
            )
        ],
        as_of=now,
        phantom_penalty_avg=0.5,
    )

    assert summary.recommendations.liquidity_haircut == round(1.0 - summary.liquidity_reliability.lower_bound, 6)
    assert summary.recommendations.execution_probability_floor == summary.fill_reliability.lower_bound
    assert summary.recommendations.competition_risk_multiplier == round(
        1.0 + (1.0 - summary.competition_reliability.lower_bound),
        6,
    )
    assert summary.recommendations.expected_slippage_multiplier == 1.5
