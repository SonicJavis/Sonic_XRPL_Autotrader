from app.calibration.regime_classifier import RegimeClassificationInput, XRPLRegimeClassifier


def test_detects_illusion_liquidity_regime() -> None:
    result = XRPLRegimeClassifier().classify(
        metrics=RegimeClassificationInput(
            visible_depth_score=0.9,
            execution_survivability_error=0.75,
            slippage_underestimation=0.3,
            depth_overestimation=0.8,
            volatility_score=0.4,
            decay_score=0.4,
            wall_flicker_rate=0.2,
            inclusion_uncertainty=0.2,
        )
    )
    assert result.regime == "ILLUSION_LIQUIDITY"
    assert result.xrpl_flags["depth_illusion_risk"] is True


def test_detects_path_distorted_regime() -> None:
    result = XRPLRegimeClassifier().classify(
        metrics=RegimeClassificationInput(
            visible_depth_score=0.7,
            execution_survivability_error=0.2,
            slippage_underestimation=0.6,
            depth_overestimation=0.2,
            volatility_score=0.2,
            decay_score=0.2,
            wall_flicker_rate=0.1,
            inclusion_uncertainty=0.2,
        )
    )
    assert result.regime == "PATH_DISTORTED"
    assert result.xrpl_flags["pathfinding_risk"] is True


def test_low_confidence_forces_all_xrpl_flags_true() -> None:
    result = XRPLRegimeClassifier().classify(
        metrics=RegimeClassificationInput(
            visible_depth_score=0.6,
            execution_survivability_error=0.1,
            slippage_underestimation=0.1,
            depth_overestimation=0.9,
            volatility_score=0.9,
            decay_score=0.8,
            wall_flicker_rate=0.8,
            inclusion_uncertainty=0.9,
        ),
        confidence_floor_threshold=0.8,
    )
    assert result.confidence < 0.8
    assert result.xrpl_flags == {
        "possible_unfunded_liquidity": True,
        "pathfinding_risk": True,
        "inclusion_uncertainty": True,
        "depth_illusion_risk": True,
    }
