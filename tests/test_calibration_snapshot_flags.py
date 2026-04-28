from app.calibration.snapshot_flags import build_xrpl_risk_flags
from app.db.models import CalibrationRecommendationSnapshot


def test_low_confidence_forces_all_xrpl_flags_true() -> None:
    flags = build_xrpl_risk_flags(
        confidence_score=0.2,
        confidence_floor_threshold=0.4,
        possible_unfunded_liquidity=False,
        pathfinding_risk=False,
        inclusion_uncertainty=False,
        depth_illusion_risk=False,
    )
    assert flags == {
        "possible_unfunded_liquidity": True,
        "pathfinding_risk": True,
        "inclusion_uncertainty": True,
        "depth_illusion_risk": True,
    }


def test_high_confidence_preserves_provided_xrpl_flags() -> None:
    flags = build_xrpl_risk_flags(
        confidence_score=0.9,
        confidence_floor_threshold=0.4,
        possible_unfunded_liquidity=True,
        pathfinding_risk=False,
        inclusion_uncertainty=True,
        depth_illusion_risk=False,
    )
    assert flags == {
        "possible_unfunded_liquidity": True,
        "pathfinding_risk": False,
        "inclusion_uncertainty": True,
        "depth_illusion_risk": False,
    }


def test_snapshot_defaults_to_pessimistic_xrpl_flags() -> None:
    row = CalibrationRecommendationSnapshot(
        queue_haircut_pct=0.2,
        drift_haircut_pct=0.2,
        latency_ms=1000,
        snapshot_max_age_ms=900,
    )
    assert row.xrpl_risk_flags_json == {
        "possible_unfunded_liquidity": True,
        "pathfinding_risk": True,
        "inclusion_uncertainty": True,
        "depth_illusion_risk": True,
    }
