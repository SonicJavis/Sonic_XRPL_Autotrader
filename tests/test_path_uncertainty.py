from app.live.path_uncertainty import PathUncertaintyInput, PathUncertaintyModel


def test_path_uncertainty_increases_with_multi_hop_and_missing_ledgers() -> None:
    model = PathUncertaintyModel()
    result = model.evaluate(
        PathUncertaintyInput(
            direct_book_depth_xrp=0.0,
            autobridged_book_depth_xrp=800.0,
            route_count=3,
            top_of_book_churn=0.8,
            snapshot_age_ms=2500,
            ledger_delay_error=0.5,
            missing_ledger_ratio=0.6,
        )
    )

    assert result.multi_hop_risk > 0.5
    assert result.route_instability > 0.5
    assert result.path_distortion_likelihood > 0.5
    assert result.path_execution_risk > 0.5
    assert result.route_confidence < 0.5


def test_path_uncertainty_stays_lower_for_stable_direct_pair() -> None:
    model = PathUncertaintyModel()
    result = model.evaluate(
        PathUncertaintyInput(
            direct_book_depth_xrp=900.0,
            autobridged_book_depth_xrp=950.0,
            route_count=1,
            top_of_book_churn=0.1,
            snapshot_age_ms=300,
            ledger_delay_error=0.05,
            missing_ledger_ratio=0.0,
        )
    )

    assert result.path_execution_risk < 0.3
    assert result.route_confidence > 0.7