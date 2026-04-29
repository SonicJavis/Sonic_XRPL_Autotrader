from __future__ import annotations

from statistics import mean

from app.validation.xrpl_validation_models import XRPLObservedOutcomeWindow, XRPLShadowPrediction, XRPLValidationResult


def _unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _avg(values: list[float]) -> float:
    return mean(values) if values else 0.0


def compare_prediction_to_window(prediction: XRPLShadowPrediction, window: XRPLObservedOutcomeWindow) -> XRPLValidationResult:
    requested_size = max(prediction.requested_size, prediction.predicted_effective_size, 1e-9)
    window_length = max(1, int(window.end_ledger) - int(window.start_ledger) + 1)
    realized_fill_probability = _unit(window.avg_possible_fill / requested_size)
    realized_outcome_binary = 1.0 if window.avg_possible_fill > 0.0 else 0.0
    fill_probability_error = abs(prediction.predicted_probability - realized_fill_probability)
    effective_size_error = _unit(abs(prediction.predicted_effective_size - window.avg_possible_fill) / requested_size)
    ev_scale = max(abs(prediction.predicted_ev), requested_size, 1.0)
    observed_ev_proxy = window.avg_possible_fill - requested_size
    ev_error = _unit(abs(prediction.predicted_ev - observed_ev_proxy) / ev_scale)
    liquidity_disappearance = _unit(max(0.0, prediction.predicted_liquidity - window.max_possible_fill) / max(prediction.predicted_liquidity, 1.0))
    path_failure_rate = _unit(window.route_changes_count / window_length)
    competition_miss_rate = _unit(window.competition_events_proxy * (1.0 - prediction.predicted_competition_penalty))
    latency_miss = _unit(abs(prediction.predicted_latency_ms - _avg(window.latency_distribution_ms)) / 10000.0)
    regime_mismatch = _infer_window_regime(window) != prediction.predicted_regime
    brier_score = _unit((prediction.predicted_probability - realized_outcome_binary) ** 2)
    disagreement_score = _unit(
        fill_probability_error * 0.25
        + effective_size_error * 0.20
        + ev_error * 0.15
        + liquidity_disappearance * 0.15
        + path_failure_rate * 0.10
        + competition_miss_rate * 0.10
        + latency_miss * 0.05
    )
    realized_accuracy = 1.0 - disagreement_score
    confidence_error = abs(prediction.predicted_confidence - realized_accuracy)
    return XRPLValidationResult(
        decision_id=prediction.decision_id,
        fill_probability_error=fill_probability_error,
        effective_size_error=effective_size_error,
        ev_error=ev_error,
        liquidity_disappearance=liquidity_disappearance,
        path_failure_rate=path_failure_rate,
        competition_miss_rate=competition_miss_rate,
        latency_miss=latency_miss,
        regime_mismatch=regime_mismatch,
        disagreement_score=disagreement_score,
        brier_score=brier_score,
        overconfidence_flag=prediction.predicted_probability > 0.7 and realized_fill_probability < 0.3,
        underconfidence_flag=prediction.predicted_probability < 0.3 and realized_fill_probability > 0.7,
        confidence_error=confidence_error,
        error_attribution=_attribute_error(
            {
                "liquidity_illusion": liquidity_disappearance + fill_probability_error,
                "latency": latency_miss,
                "path_instability": path_failure_rate,
                "competition": competition_miss_rate,
                "regime_shift": 1.0 if regime_mismatch else 0.0,
            }
        ),
    )


def _infer_window_regime(window: XRPLObservedOutcomeWindow) -> str:
    if window.avg_possible_fill <= 0.0:
        return "EXECUTION_COLLAPSE"
    if window.route_changes_count > 0:
        return "ROUTE_UNSTABLE"
    if window.competition_events_proxy >= 0.5:
        return "COMPETITION_SPIKE"
    if _avg(window.latency_distribution_ms) > 5000:
        return "LATENCY_DOMINATED"
    return "STABLE_SHADOW"


def _attribute_error(errors: dict[str, float]) -> str:
    return sorted(errors.items(), key=lambda item: (-item[1], item[0]))[0][0]
