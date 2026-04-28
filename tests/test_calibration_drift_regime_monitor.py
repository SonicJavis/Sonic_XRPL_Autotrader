from app.calibration.drift_regime_monitor import DriftRegimeMonitor


def test_escalates_alert_for_worsening_drift_and_instability() -> None:
    out = DriftRegimeMonitor().assess(
        drift_errors=[0.2, 0.4, 0.6, 0.8],
        regimes=["STABLE", "THIN", "PATH_DISTORTED", "COLLAPSING"],
    )
    assert out.regime_transition_rate > 0.5
    assert out.instability_score > 0.5
    assert out.alert_level == "CRITICAL"


def test_low_instability_remains_low_alert() -> None:
    out = DriftRegimeMonitor().assess(
        drift_errors=[0.1, 0.1, 0.09, 0.1],
        regimes=["STABLE", "STABLE", "STABLE", "STABLE"],
    )
    assert out.regime_transition_rate == 0.0
    assert out.instability_score < 0.3
    assert out.alert_level == "LOW"
