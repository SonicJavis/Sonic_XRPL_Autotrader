from app.validation.dual_error_engine import DualErrorEngine, DualErrorInput


def test_low_confidence_observation_suppresses_false_flags() -> None:
    out = DualErrorEngine().evaluate(
        DualErrorInput(
            simulator_fillable=True,
            simulator_fill_ratio=0.9,
            observed_depth_present=True,
            observation_confidence=0.25,
            observed_fill_probability=0.8,
        )
    )
    assert out.observation_uncertain is True
    assert out.false_confidence_flag is False


def test_high_confidence_mismatch_triggers_false_confidence() -> None:
    out = DualErrorEngine().evaluate(
        DualErrorInput(
            simulator_fillable=True,
            simulator_fill_ratio=0.95,
            observed_depth_present=False,
            observation_confidence=0.9,
            observed_fill_probability=0.1,
        )
    )
    assert out.disagreement_score > 0.55
    assert out.false_confidence_flag is True


def test_both_uncertain_makes_no_judgement() -> None:
    out = DualErrorEngine().evaluate(
        DualErrorInput(
            simulator_fillable=False,
            simulator_fill_ratio=0.05,
            observed_depth_present=False,
            observation_confidence=0.2,
            observed_fill_probability=0.05,
        )
    )
    assert out.simulator_uncertain is True
    assert out.observation_uncertain is True
    assert out.false_confidence_flag is False
    assert out.confidence_weighted_error < 0.2
