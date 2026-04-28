from app.calibration.xrpl_memory_model import XRPLMemoryAggregate
from app.calibration.xrpl_regime_detector import XRPLRegimeAssessment
from app.decision.xrpl_memory_weighting import XRPLMemoryWeighting, XRPLMemoryWeightingInput


def _aggregate(**overrides) -> XRPLMemoryAggregate:
    values = {
        "scope": "global",
        "key": "all",
        "sample_count": 3,
        "avg_phantom_penalty": 0.05,
        "avg_liquidity_decay": 0.9,
        "avg_route_instability": 0.05,
        "avg_path_complexity": 1.0,
        "avg_routes_seen_count": 1.0,
        "avg_latency_seconds": 4.0,
        "avg_competition_penalty": 0.05,
        "avg_low_fill_bias": 0.05,
        "avg_drift": 0.0,
        "avg_drift_adjusted_ev": 0.4,
        "avg_effective_fill_probability": 0.8,
        "liquidity_reliability": 0.9,
        "execution_reliability": 0.85,
        "regime_pressure_score": 0.1,
        "advisory_risk_level": "LOW",
    }
    values.update(overrides)
    return XRPLMemoryAggregate(**values)


def _regime(regime: str = "STABLE_SHADOW", flags: list[str] | None = None, severity: float = 0.1) -> XRPLRegimeAssessment:
    return XRPLRegimeAssessment(
        regime=regime,
        severity_score=severity,
        risk_flags=flags or [],
        advisory_only=True,
        is_shadow=True,
        is_executable=False,
    )


def _input(**overrides) -> XRPLMemoryWeightingInput:
    values = {
        "global_aggregate": _aggregate(),
        "token_aggregate": None,
        "issuer_aggregate": None,
        "global_regime": _regime(),
        "token_regime": None,
        "issuer_regime": None,
    }
    values.update(overrides)
    return XRPLMemoryWeightingInput(**values)


def test_low_risk_memory_is_near_neutral() -> None:
    result = XRPLMemoryWeighting().evaluate(_input())

    assert 0.0 <= result.execution_probability_multiplier <= 1.0
    assert 0.0 <= result.effective_size_multiplier <= 1.0
    assert result.slippage_multiplier_boost >= 1.0
    assert result.ev_penalty >= 0.0
    assert result.advisory_risk_level == "LOW"


def test_token_critical_risk_reduces_probability_and_size() -> None:
    result = XRPLMemoryWeighting().evaluate(
        _input(
            token_aggregate=_aggregate(
                scope="token",
                key="7",
                advisory_risk_level="CRITICAL",
                regime_pressure_score=0.95,
                liquidity_reliability=0.1,
                execution_reliability=0.08,
                avg_phantom_penalty=0.8,
            )
        )
    )

    assert result.advisory_risk_level == "CRITICAL"
    assert result.execution_probability_multiplier < 0.5
    assert result.effective_size_multiplier < 0.5


def test_issuer_high_risk_reduces_effective_size() -> None:
    neutral = XRPLMemoryWeighting().evaluate(_input())
    high = XRPLMemoryWeighting().evaluate(
        _input(
            issuer_aggregate=_aggregate(
                scope="issuer",
                key="rIssuer",
                advisory_risk_level="HIGH",
                liquidity_reliability=0.25,
                avg_phantom_penalty=0.45,
                regime_pressure_score=0.65,
            )
        )
    )

    assert high.effective_size_multiplier < neutral.effective_size_multiplier


def test_regime_flags_map_to_memory_flags() -> None:
    result = XRPLMemoryWeighting().evaluate(
        _input(
            token_regime=_regime("LIQUIDITY_ILLUSION", severity=0.9),
            issuer_regime=_regime("ROUTE_UNSTABLE", flags=["PATH_FAILURE_RISK", "ISSUER_RISK_PROXY", "LIQUIDITY_FRAGMENTATION"]),
        )
    )

    assert "PHANTOM_LIQUIDITY_MEMORY" in result.risk_flags
    assert "ROUTE_MEMORY_UNSTABLE" in result.risk_flags
    assert "PATH_MEMORY_FAILURE" in result.risk_flags
    assert "ISSUER_MEMORY_RISK" in result.risk_flags
    assert "LIQUIDITY_MEMORY_FRAGMENTED" in result.risk_flags


def test_execution_collapse_memory_is_strongly_penalised() -> None:
    result = XRPLMemoryWeighting().evaluate(_input(global_regime=_regime("EXECUTION_COLLAPSE", severity=1.0)))

    assert "EXECUTION_MEMORY_COLLAPSE" in result.risk_flags
    assert result.execution_probability_multiplier <= 0.1
    assert result.effective_size_multiplier <= 0.1
    assert result.ev_penalty >= 1.0


def test_weighting_is_deterministic() -> None:
    data = _input(
        token_aggregate=_aggregate(scope="token", key="1", advisory_risk_level="MEDIUM", avg_route_instability=0.3),
        token_regime=_regime("COMPETITION_SPIKE", severity=0.8),
    )

    first = XRPLMemoryWeighting().evaluate(data)
    second = XRPLMemoryWeighting().evaluate(data)

    assert first == second
