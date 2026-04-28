from app.calibration.xrpl_memory_model import XRPLMemoryAggregate
from app.calibration.xrpl_regime_detector import XRPLRegimeDetector


def _aggregate(**overrides) -> XRPLMemoryAggregate:
    values = {
        "scope": "global",
        "key": "all",
        "sample_count": 3,
        "avg_phantom_penalty": 0.05,
        "avg_liquidity_decay": 0.9,
        "avg_route_instability": 0.05,
        "avg_path_complexity": 0.0,
        "avg_latency_seconds": 4.0,
        "avg_competition_penalty": 0.05,
        "avg_low_fill_bias": 0.05,
        "avg_drift": 0.0,
        "avg_drift_adjusted_ev": 0.5,
        "avg_effective_fill_probability": 0.8,
        "liquidity_reliability": 0.85,
        "execution_reliability": 0.75,
        "regime_pressure_score": 0.10,
        "advisory_risk_level": "LOW",
    }
    values.update(overrides)
    return XRPLMemoryAggregate(**values)


def _assert_meta(regime: str, **overrides) -> None:
    result = XRPLRegimeDetector().assess(_aggregate(**overrides))
    assert result.regime == regime
    assert 0.0 <= result.severity_score <= 1.0
    assert result.advisory_only is True
    assert result.is_shadow is True
    assert result.is_executable is False


def test_stable_shadow_detection() -> None:
    _assert_meta("STABLE_SHADOW")


def test_liquidity_illusion_detection() -> None:
    _assert_meta(
        "LIQUIDITY_ILLUSION",
        avg_phantom_penalty=0.8,
        avg_liquidity_decay=0.1,
        liquidity_reliability=0.02,
        regime_pressure_score=0.7,
    )


def test_unstable_routing_detection() -> None:
    _assert_meta("ROUTE_UNSTABLE", avg_route_instability=0.7, avg_path_complexity=2.5)


def test_competition_spike_detection() -> None:
    _assert_meta("COMPETITION_SPIKE", avg_competition_penalty=0.8, avg_low_fill_bias=0.4)


def test_latency_dominated_detection() -> None:
    _assert_meta("LATENCY_DOMINATED", avg_latency_seconds=16.0)


def test_drift_risk_detection() -> None:
    _assert_meta("DRIFT_RISK", avg_drift=0.12, avg_drift_adjusted_ev=-0.2)


def test_execution_collapse_detection() -> None:
    _assert_meta("EXECUTION_COLLAPSE", avg_effective_fill_probability=0.02, execution_reliability=0.02)
