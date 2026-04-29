from datetime import datetime, timezone

from app.validation.xrpl_validation_engine import _attribute_error, compare_prediction_to_window
from app.validation.xrpl_validation_models import XRPLObservedOutcomeWindow, XRPLShadowPrediction


def _prediction(**kwargs) -> XRPLShadowPrediction:
    data = {
        "decision_id": 1,
        "token_id": 1,
        "issuer": "rIssuer",
        "ledger_index_start": 10,
        "predicted_probability": 0.5,
        "predicted_effective_size": 50.0,
        "predicted_ev": 0.0,
        "predicted_path_complexity": 1,
        "predicted_route_instability": 0.1,
        "predicted_competition_penalty": 0.5,
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
        "start_ledger": 11,
        "end_ledger": 13,
        "max_possible_fill": 50.0,
        "min_possible_fill": 50.0,
        "avg_possible_fill": 50.0,
        "liquidity_decay_curve": [0.5],
        "price_drift_curve": [0.0],
        "route_changes_count": 0,
        "competition_events_proxy": 0.0,
        "latency_distribution_ms": [4000.0],
        "observed_at": datetime(2026, 4, 29, tzinfo=timezone.utc),
    }
    data.update(kwargs)
    return XRPLObservedOutcomeWindow(**data)


def test_attribution_dimensions_are_stable() -> None:
    cases = [
        (_prediction(predicted_liquidity=200.0, predicted_probability=0.9), _window(max_possible_fill=10.0, avg_possible_fill=10.0), "liquidity_illusion"),
        (_prediction(predicted_latency_ms=0.0, predicted_regime="LATENCY_DOMINATED"), _window(latency_distribution_ms=[10000.0]), "latency"),
        (_prediction(predicted_regime="ROUTE_UNSTABLE"), _window(route_changes_count=3), "path_instability"),
        (_prediction(predicted_competition_penalty=0.0, predicted_regime="COMPETITION_SPIKE"), _window(competition_events_proxy=1.0), "competition"),
        (_prediction(predicted_regime="DRIFT_RISK"), _window(), "regime_shift"),
    ]

    for prediction, window, attribution in cases:
        result = compare_prediction_to_window(prediction, window)
        assert result.error_attribution == attribution
        assert result.error_attribution != "unknown"


def test_attribution_tie_break_is_deterministic() -> None:
    assert _attribute_error({"latency": 0.5, "competition": 0.5, "regime_shift": 0.1}) == "competition"
    assert _attribute_error({"latency": 0.5, "competition": 0.5, "regime_shift": 0.1}) == "competition"
