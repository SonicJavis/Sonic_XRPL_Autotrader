from app.validation.observation_uncertainty import ObservationSample, ObservationUncertaintyModel


def test_stable_book_has_higher_confidence() -> None:
    samples = [
        ObservationSample(600.0, 620.0, 0.8, 0.99, 1.00, 0.995),
        ObservationSample(610.0, 615.0, 0.82, 0.989, 1.001, 0.995),
        ObservationSample(605.0, 618.0, 0.79, 0.99, 1.0, 0.995),
        ObservationSample(608.0, 617.0, 0.81, 0.99, 1.001, 0.995),
    ]
    out = ObservationUncertaintyModel().evaluate(samples)
    assert out.depth_reliability_score > 0.6
    assert out.observation_confidence > 0.55


def test_flickering_book_has_low_confidence() -> None:
    samples = [
        ObservationSample(700.0, 700.0, 1.0, 0.99, 1.01, 1.0),
        ObservationSample(150.0, 120.0, 2.8, 1.03, 1.00, 0.95),
        ObservationSample(680.0, 690.0, 0.9, 0.995, 1.005, 0.995),
        ObservationSample(100.0, 90.0, 3.1, 1.02, 0.99, 0.93),
    ]
    out = ObservationUncertaintyModel().evaluate(samples)
    assert out.path_distortion_risk > 0.5
    assert out.fundedness_uncertainty > 0.45
    assert out.observation_confidence < 0.45


def test_empty_book_has_near_zero_confidence() -> None:
    out = ObservationUncertaintyModel().evaluate([])
    assert out.depth_reliability_score == 0.0
    assert out.observation_confidence <= 0.05
