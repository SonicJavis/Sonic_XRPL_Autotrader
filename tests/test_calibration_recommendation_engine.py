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
