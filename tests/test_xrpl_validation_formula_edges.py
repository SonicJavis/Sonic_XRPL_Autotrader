from datetime import datetime, timezone
from math import inf, isfinite, nan

from app.validation.xrpl_validation_engine import compare_prediction_to_window
from app.validation.xrpl_validation_models import XRPLObservedOutcomeWindow, XRPLShadowPrediction


def _prediction(**kwargs) -> XRPLShadowPrediction:
    data = {
        "decision_id": 1,
        "token_id": 1,
        "issuer": "rIssuer",
        "ledger_index_start": 1,
        "predicted_probability": 0.5,
        "predicted_effective_size": 50.0,
        "predicted_ev": 0.0,
        "predicted_path_complexity": 1,
        "predicted_route_instability": 0.1,
        "predicted_competition_penalty": 0.1,
        "predicted_regime": "STABLE_SHADOW",
        "predicted_confidence": 0.5,
        "created_at": datetime(2026, 4, 29, tzinfo=timezone.utc),
        "requested_size": 100.0,
        "predicted_liquidity": 100.0,
        "predicted_latency_ms": 4000.0,
    }
    data.update(kwargs)
    return XRPLShadowPrediction(**data)


def _window(**kwargs) -> XRPLObservedOutcomeWindow:
    data = {
        "token_id": 1,
        "issuer": "rIssuer",
        "start_ledger": 2,
        "end_ledger": 4,
        "max_possible_fill": 80.0,
        "min_possible_fill": 10.0,
        "avg_possible_fill": 40.0,
        "liquidity_decay_curve": [0.8, 0.4, 0.1],
        "price_drift_curve": [0.0, 0.01, -0.01],
        "route_changes_count": 1,
        "competition_events_proxy": 0.2,
        "latency_distribution_ms": [3000.0, 4000.0],
        "observed_at": datetime(2026, 4, 29, tzinfo=timezone.utc),
    }
    data.update(kwargs)
    return XRPLObservedOutcomeWindow(**data)


def test_formula_edges_are_finite_and_bounded() -> None:
    cases = [
        (_prediction(requested_size=0, predicted_effective_size=0), _window()),
        (_prediction(predicted_probability=nan), _window()),
        (_prediction(predicted_probability=inf), _window()),
        (_prediction(predicted_effective_size=nan), _window()),
        (_prediction(predicted_effective_size=inf), _window()),
        (_prediction(predicted_ev=nan), _window()),
        (_prediction(predicted_ev=inf), _window()),
        (_prediction(predicted_ev=-100.0), _window()),
        (_prediction(predicted_ev=10**12), _window()),
        (_prediction(), _window(max_possible_fill=10.0, avg_possible_fill=100.0)),
        (_prediction(), _window(latency_distribution_ms=[])),
    ]

    for prediction, window in cases:
        result = compare_prediction_to_window(prediction, window)
        assert all(isfinite(value) for value in _result_numbers(result))
        assert all(0.0 <= value <= 1.0 for value in _result_numbers(result))


def test_observed_window_clamps_fill_to_window_bounds() -> None:
    window = _window(max_possible_fill=10.0, min_possible_fill=20.0, avg_possible_fill=50.0)

    assert window.max_possible_fill == 10.0
    assert window.min_possible_fill == 10.0
    assert window.avg_possible_fill == 10.0


def _result_numbers(result) -> list[float]:
    return [
        result.fill_probability_error,
        result.effective_size_error,
        result.ev_error,
        result.liquidity_disappearance,
        result.path_failure_rate,
        result.competition_miss_rate,
        result.latency_miss,
        result.disagreement_score,
        result.brier_score,
        result.confidence_error,
    ]
