from datetime import datetime, timezone
from math import isfinite

import pytest

from app.validation.xrpl_validation_engine import compare_prediction_to_window
from app.validation.xrpl_validation_models import XRPLObservedOutcomeWindow, XRPLShadowPrediction


def _prediction(**kwargs) -> XRPLShadowPrediction:
    data = {
        "decision_id": 1,
        "token_id": 1,
        "issuer": "rIssuer",
        "ledger_index_start": 100,
        "predicted_probability": 0.8,
        "predicted_effective_size": 80.0,
        "predicted_ev": 10.0,
        "predicted_path_complexity": 1,
        "predicted_route_instability": 0.1,
        "predicted_competition_penalty": 0.1,
        "predicted_regime": "STABLE_SHADOW",
        "predicted_confidence": 0.8,
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
        "start_ledger": 101,
        "end_ledger": 103,
        "max_possible_fill": 90.0,
        "min_possible_fill": 50.0,
        "avg_possible_fill": 70.0,
        "liquidity_decay_curve": [0.9, 0.7, 0.5],
        "price_drift_curve": [0.01, -0.01, 0.02],
        "route_changes_count": 1,
        "competition_events_proxy": 0.4,
        "latency_distribution_ms": [3000.0, 4000.0, 5000.0],
        "observed_at": datetime(2026, 4, 29, tzinfo=timezone.utc),
    }
    data.update(kwargs)
    return XRPLObservedOutcomeWindow(**data)


def test_brier_score_and_errors_are_bounded() -> None:
    result = compare_prediction_to_window(_prediction(predicted_probability=0.8), _window(avg_possible_fill=0.0, max_possible_fill=0.0))

    assert result.brier_score == pytest.approx(0.64)
    assert result.overconfidence_flag is True
    assert all(isfinite(value) and 0.0 <= value <= 1.0 for value in _numeric_values(result))
    assert result.is_truth is False
    assert result.is_executable is False


def test_underconfidence_and_liquidity_disappearance() -> None:
    result = compare_prediction_to_window(
        _prediction(predicted_probability=0.2, predicted_liquidity=120.0),
        _window(avg_possible_fill=90.0, max_possible_fill=100.0),
    )

    assert result.underconfidence_flag is True
    assert result.liquidity_disappearance > 0.0
    assert result.error_attribution in {"liquidity_illusion", "latency", "path_instability", "competition", "regime_shift"}


def test_deterministic_outputs() -> None:
    pred = _prediction()
    window = _window()

    assert compare_prediction_to_window(pred, window).to_dict() == compare_prediction_to_window(pred, window).to_dict()


def _numeric_values(result):
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
