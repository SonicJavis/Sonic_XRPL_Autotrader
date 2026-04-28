from app.calibration.recommendation_engine import CalibrationErrorSample, ConfidenceWeightedCalibrationEngine


def test_low_samples_returns_no_recommendation() -> None:
    samples = [
        CalibrationErrorSample(0.3, 0.2, 0.2, 0.1),
        CalibrationErrorSample(0.2, 0.3, 0.2, 0.1),
        CalibrationErrorSample(0.1, 0.2, 0.1, 0.1),
    ]
    out = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.8,
        sequence_stability=0.8,
    )
    assert out is None


def test_high_volatility_recommends_stricter_config() -> None:
    base_samples = [
        CalibrationErrorSample(0.8, 0.7, 0.75, 0.8),
        CalibrationErrorSample(0.7, 0.65, 0.70, 0.75),
        CalibrationErrorSample(0.85, 0.8, 0.78, 0.82),
        CalibrationErrorSample(0.72, 0.68, 0.71, 0.76),
        CalibrationErrorSample(0.80, 0.73, 0.74, 0.79),
        CalibrationErrorSample(0.77, 0.69, 0.72, 0.78),
    ]
    samples = base_samples + base_samples
    out = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.6,
        sequence_stability=0.6,
    )
    assert out is not None
    assert out.queue_haircut_pct >= 0.30
    assert out.drift_haircut_pct >= 0.25
    assert out.latency_ms >= 1000
    assert out.snapshot_max_age_ms <= 1400


def test_regime_rules_harden_specific_penalties() -> None:
    samples = [CalibrationErrorSample(0.6, 0.7, 0.7, 0.6)] * 12

    base = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.8,
        sequence_stability=0.8,
    )
    assert base is not None

    path = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.8,
        sequence_stability=0.8,
        regime="PATH_DISTORTED",
    )
    assert path is not None
    assert path.slippage_penalty_pct >= base.slippage_penalty_pct

    illusion = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.8,
        sequence_stability=0.8,
        regime="ILLUSION_LIQUIDITY",
    )
    assert illusion is not None
    assert illusion.queue_haircut_pct >= base.queue_haircut_pct

    collapsing = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.8,
        sequence_stability=0.8,
        regime="COLLAPSING",
    )
    assert collapsing is not None
    assert collapsing.drift_haircut_pct >= base.drift_haircut_pct
    assert collapsing.latency_ms >= base.latency_ms


def test_engine_never_reduces_existing_penalties() -> None:
    samples = [CalibrationErrorSample(0.3, 0.2, 0.2, 0.2)] * 20
    out = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.9,
        sequence_stability=0.9,
        current_slippage_penalty_pct=0.30,
        current_queue_haircut_pct=0.40,
        current_drift_haircut_pct=0.35,
        current_latency_ms=1800,
        current_snapshot_max_age_ms=800,
    )
    assert out is not None
    assert out.slippage_penalty_pct >= 0.30
    assert out.queue_haircut_pct >= 0.40
    assert out.drift_haircut_pct >= 0.35
    assert out.latency_ms >= 1800
    assert out.snapshot_max_age_ms <= 800


def test_confidence_hardening_blocks_output_under_instability() -> None:
    samples = [CalibrationErrorSample(0.4, 0.4, 0.4, 0.4)] * 10
    out = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.7,
        sequence_stability=0.7,
        confidence_floor_threshold=0.45,
        regime_transition_rate=0.9,
        drift_error=0.9,
        inclusion_uncertainty=0.9,
    )
    assert out is None


def test_confidence_floor_threshold_is_enforced() -> None:
    samples = [CalibrationErrorSample(0.3, 0.3, 0.3, 0.3)] * 20
    out = ConfidenceWeightedCalibrationEngine().recommend(
        samples=samples,
        fundedness_confidence=0.7,
        sequence_stability=0.7,
        confidence_floor_threshold=0.8,
    )
    assert out is None
