from app.calibration.xrpl_shadow_error_model import XRPLShadowErrorInput, XRPLShadowErrorModel


def test_xrpl_shadow_error_model_applies_phantom_route_and_competition_penalties() -> None:
    result = XRPLShadowErrorModel().evaluate(
        XRPLShadowErrorInput(
            requested_size=100.0,
            simulated_fill_ratio=0.8,
            observed_fill_ratio=0.1,
            snapshot_derived_liquidity=150.0,
            observed_possible_fill=20.0,
            price_error_norm=0.2,
            liquidity_error=0.3,
            ledger_delay_error=0.4,
            path_error=0.5,
            observation_confidence=0.8,
            route_confidence=0.4,
            unique_routes_seen=3,
            total_snapshots=4,
        )
    )

    assert result.phantom_liquidity == 130.0
    assert result.phantom_penalty == 1.0
    assert result.route_instability == 0.75
    assert result.competition_penalty == 1.0
    assert result.fill_variance == 0.7
    assert result.low_fill_bias == 0.7
    assert result.fill_disagreement == 0.7
    assert result.raw_error == 0.565
    assert result.weighted_error == 0.678


def test_xrpl_shadow_error_model_falls_back_to_route_confidence_when_routes_not_observed() -> None:
    result = XRPLShadowErrorModel().evaluate(
        XRPLShadowErrorInput(
            requested_size=50.0,
            simulated_fill_ratio=0.2,
            observed_fill_ratio=0.2,
            snapshot_derived_liquidity=30.0,
            observed_possible_fill=20.0,
            price_error_norm=0.0,
            liquidity_error=0.1,
            ledger_delay_error=0.1,
            path_error=0.2,
            observation_confidence=0.9,
            route_confidence=0.8,
            unique_routes_seen=0,
            total_snapshots=0,
        )
    )

    assert result.route_instability == 0.2
    assert result.competition_penalty == 0.0
