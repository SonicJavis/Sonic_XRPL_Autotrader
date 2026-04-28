from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from math import exp, sqrt

from app.calibration.xrpl_shadow_error_model import XRPLShadowErrorInput, XRPLShadowErrorMetrics, XRPLShadowErrorModel
from app.feedback.decision_outcome import DecisionOutcomeModel, build_decision_outcome_from_shadow_execution
from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot


def _clamp_unit(raw: float) -> float:
    return max(0.0, min(1.0, float(raw)))


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _execution_details(row: ExecutionRecord) -> dict[str, object]:
    try:
        return json.loads(str(row.execution_details_json or "{}"))
    except json.JSONDecodeError:
        return {}


def _is_shadow_execution(row: ExecutionRecord) -> bool:
    return bool(_execution_details(row).get("shadow"))


@dataclass(slots=True)
class XRPLBayesianObservation:
    observed_at: datetime
    sample_weight: float
    phantom_penalty: float
    route_instability: float
    competition_penalty: float
    fill_disagreement: float
    low_fill_bias: float
    liquidity_error: float
    path_error: float
    ledger_delay_error: float
    weighted_error: float


@dataclass(slots=True)
class XRPLReliabilityDimension:
    lower_bound: float
    mean: float
    std: float
    alpha: float
    beta: float
    adaptive_weight: float


@dataclass(slots=True)
class XRPLShadowRecommendations:
    liquidity_haircut: float
    expected_slippage_multiplier: float
    execution_probability_floor: float
    competition_risk_multiplier: float


@dataclass(slots=True)
class XRPLBayesianCalibrationSummary:
    sample_count: int
    decay_half_life: float
    liquidity_reliability: XRPLReliabilityDimension
    path_reliability: XRPLReliabilityDimension
    latency_reliability: XRPLReliabilityDimension
    fill_reliability: XRPLReliabilityDimension
    competition_reliability: XRPLReliabilityDimension
    recommendations: XRPLShadowRecommendations
    phantom_penalty_avg: float
    weighted_error_avg: float


@dataclass(slots=True)
class XRPLShadowCalibrationSample:
    execution_id: int
    observed_possible_fill: float
    snapshot_derived_liquidity: float
    route_confidence: float
    route_used: str | None
    observation_confidence: float
    price_error_norm: float
    liquidity_error: float
    path_error: float
    ledger_delay_error: float
    error_metrics: XRPLShadowErrorMetrics
    observation: XRPLBayesianObservation


@dataclass(slots=True)
class XRPLShadowCalibrationAggregate:
    sample_count: int
    shadow_disagreement_avg: float
    phantom_liquidity_avg: float
    phantom_penalty_avg: float
    route_instability_avg: float
    competition_failure_rate: float
    fill_variance_avg: float
    low_fill_bias_avg: float
    price_error_norm_avg: float
    liquidity_error_avg: float
    ledger_delay_error_avg: float
    path_error_avg: float
    observation_confidence_avg: float
    snapshot_derived_liquidity_avg: float
    observed_possible_fill_avg: float
    calibration: XRPLBayesianCalibrationSummary
    samples: list[XRPLShadowCalibrationSample]


class XRPLBayesianCalibrator:
    def __init__(self, *, decay_half_life: float = 300.0) -> None:
        self.decay_half_life = max(1.0, float(decay_half_life))
        self.base_weights: dict[str, float] = {
            "liquidity": 1.0,
            "path": 1.0,
            "latency": 1.0,
            "fill": 1.0,
            "competition": 1.0,
        }

    def calibrate(
        self,
        observations: list[XRPLBayesianObservation],
        *,
        as_of: datetime | None = None,
        phantom_penalty_avg: float = 0.0,
    ) -> XRPLBayesianCalibrationSummary:
        if not observations:
            zero_dimension = XRPLReliabilityDimension(
                lower_bound=0.0,
                mean=0.0,
                std=0.0,
                alpha=1.0,
                beta=1.0,
                adaptive_weight=3.0,
            )
            recommendations = XRPLShadowRecommendations(
                liquidity_haircut=1.0,
                expected_slippage_multiplier=1.0,
                execution_probability_floor=0.0,
                competition_risk_multiplier=2.0,
            )
            return XRPLBayesianCalibrationSummary(
                sample_count=0,
                decay_half_life=self.decay_half_life,
                liquidity_reliability=zero_dimension,
                path_reliability=zero_dimension,
                latency_reliability=zero_dimension,
                fill_reliability=zero_dimension,
                competition_reliability=zero_dimension,
                recommendations=recommendations,
                phantom_penalty_avg=0.0,
                weighted_error_avg=0.0,
            )

        ordered = sorted(observations, key=lambda row: _utc(row.observed_at))
        anchor_time = _utc(as_of or ordered[-1].observed_at)
        states: dict[str, dict[str, float]] = {
            key: {"alpha": 1.0, "beta": 1.0, "adaptive_weight_total": 0.0, "updates": 0.0}
            for key in self.base_weights
        }

        for observation in ordered:
            age_seconds = max(0.0, (_utc(anchor_time) - _utc(observation.observed_at)).total_seconds())
            decay_factor = exp(-age_seconds / self.decay_half_life)
            sample_weight = max(0.0, float(observation.sample_weight))
            error_scores = {
                "liquidity": _clamp_unit(max(observation.liquidity_error, observation.phantom_penalty)),
                "path": _clamp_unit(max(observation.path_error, observation.route_instability)),
                "latency": _clamp_unit(observation.ledger_delay_error),
                "fill": _clamp_unit(max(observation.fill_disagreement, observation.low_fill_bias)),
                "competition": _clamp_unit(observation.competition_penalty),
            }
            for dimension, score in error_scores.items():
                state = states[dimension]
                current = self._dimension_from_state(state)
                unreliability = 1.0 - current.lower_bound
                raw_weight = self.base_weights[dimension] * (1.0 + (2.0 * unreliability))
                success = _clamp_unit(1.0 - score)
                failure = _clamp_unit(1.0 - success)
                increment = decay_factor * sample_weight * raw_weight
                state["alpha"] += increment * success
                state["beta"] += increment * failure
                state["adaptive_weight_total"] += raw_weight
                state["updates"] += 1.0

        liquidity_dimension = self._dimension_from_state(states["liquidity"])
        path_dimension = self._dimension_from_state(states["path"])
        latency_dimension = self._dimension_from_state(states["latency"])
        fill_dimension = self._dimension_from_state(states["fill"])
        competition_dimension = self._dimension_from_state(states["competition"])
        recommendations = XRPLShadowRecommendations(
            liquidity_haircut=round(1.0 - liquidity_dimension.lower_bound, 6),
            expected_slippage_multiplier=round(1.0 + max(0.0, float(phantom_penalty_avg)), 6),
            execution_probability_floor=round(fill_dimension.lower_bound, 6),
            competition_risk_multiplier=round(1.0 + (1.0 - competition_dimension.lower_bound), 6),
        )
        weighted_error_avg = round(sum(float(row.weighted_error) for row in ordered) / len(ordered), 6)
        return XRPLBayesianCalibrationSummary(
            sample_count=len(ordered),
            decay_half_life=self.decay_half_life,
            liquidity_reliability=liquidity_dimension,
            path_reliability=path_dimension,
            latency_reliability=latency_dimension,
            fill_reliability=fill_dimension,
            competition_reliability=competition_dimension,
            recommendations=recommendations,
            phantom_penalty_avg=round(max(0.0, float(phantom_penalty_avg)), 6),
            weighted_error_avg=weighted_error_avg,
        )

    @staticmethod
    def _dimension_from_state(state: dict[str, float]) -> XRPLReliabilityDimension:
        alpha = max(1e-9, float(state["alpha"]))
        beta = max(1e-9, float(state["beta"]))
        total = alpha + beta
        mean = alpha / total
        variance = (alpha * beta) / ((total * total) * (total + 1.0))
        std = sqrt(max(0.0, variance))
        lower_bound = max(0.0, min(1.0, mean - (1.645 * std)))
        updates = max(1.0, float(state["updates"] or 1.0))
        adaptive_weight = float(state["adaptive_weight_total"] or 0.0) / updates
        return XRPLReliabilityDimension(
            lower_bound=round(lower_bound, 6),
            mean=round(mean, 6),
            std=round(std, 6),
            alpha=round(alpha, 6),
            beta=round(beta, 6),
            adaptive_weight=round(adaptive_weight, 6),
        )


def build_xrpl_shadow_calibration_sample(
    *,
    execution: ExecutionRecord,
    snapshots: list[XRPLOrderbookSnapshot],
    error_model: XRPLShadowErrorModel | None = None,
) -> XRPLShadowCalibrationSample:
    model = error_model or XRPLShadowErrorModel()
    details = _execution_details(execution)
    requested_size = max(0.0, float(execution.requested_size or 0.0))
    simulated_fill_ratio = 0.0 if requested_size <= 0 else _clamp_unit(float(execution.filled_size or 0.0) / requested_size)

    observed_fill_ratio = _clamp_unit(float(details.get("observed_fill_ratio", simulated_fill_ratio)))
    observed_possible_fill = min(requested_size, max(0.0, float(details.get("observed_possible_fill", observed_fill_ratio * requested_size))))
    path_error = _clamp_unit(float(details.get("path_execution_risk", 0.0)))
    route_confidence = _clamp_unit(float(details.get("route_confidence", max(0.0, 1.0 - path_error))))
    observation_confidence = _clamp_unit(float(details.get("observation_confidence", 0.25)))
    route_used: str | None = None
    raw_route_used = details.get("route_used")
    if isinstance(raw_route_used, str) and raw_route_used:
        route_used = raw_route_used

    ordered_snapshots = sorted(snapshots, key=lambda row: int(row.ledger_index))
    side_is_buy = str(execution.side).upper() == "BUY"
    side_depths = [max(0.0, float(row.ask_depth_xrp if side_is_buy else row.bid_depth_xrp)) for row in ordered_snapshots]
    snapshot_derived_liquidity = max(side_depths) if side_depths else max(0.0, float(details.get("snapshot_derived_liquidity", observed_possible_fill)))

    if ordered_snapshots:
        if side_is_buy:
            reference_price = max(float(row.best_ask) for row in ordered_snapshots)
        else:
            reference_price = min(float(row.best_bid) for row in ordered_snapshots)
    else:
        reference_price = max(0.0, float(execution.avg_fill_price or 0.0))
    simulated_price = max(0.0, float(execution.avg_fill_price or reference_price))
    price_error_norm = 0.0 if reference_price <= 0 else _clamp_unit(abs(simulated_price - reference_price) / reference_price)

    snapshot_liquidity_ref = min(requested_size, snapshot_derived_liquidity) if requested_size > 0 else snapshot_derived_liquidity
    liquidity_error = 0.0 if requested_size <= 0 else _clamp_unit(abs(snapshot_liquidity_ref - observed_possible_fill) / requested_size)

    if ordered_snapshots:
        expected_delay = max(0, int(execution.ledger_index_inclusion) - int(execution.ledger_index_snapshot))
        observed_span = max(0, int(ordered_snapshots[-1].ledger_index) - int(ordered_snapshots[0].ledger_index))
        fallback_delay_error = abs(expected_delay - observed_span) / max(1.0, float(max(expected_delay, observed_span, 1)))
        observed_at = _utc(ordered_snapshots[-1].observed_at)
    else:
        fallback_delay_error = 0.0
        observed_at = _utc(execution.execution_time)
    ledger_delay_error = _clamp_unit(float(details.get("ledger_delay_error", fallback_delay_error)))

    routes_seen = details.get("routes_seen", [])
    unique_routes_seen = 0
    total_snapshots = len(ordered_snapshots)
    if isinstance(routes_seen, list) and routes_seen:
        if route_used is None:
            route_used = str(routes_seen[0])
        unique_routes_seen = len({str(route) for route in routes_seen})
    else:
        route_count = details.get("route_count")
        if route_count is not None:
            unique_routes_seen = max(0, int(route_count))
            total_snapshots = max(total_snapshots, unique_routes_seen)

    error_metrics = model.evaluate(
        XRPLShadowErrorInput(
            requested_size=requested_size,
            simulated_fill_ratio=simulated_fill_ratio,
            observed_fill_ratio=observed_fill_ratio,
            snapshot_derived_liquidity=snapshot_derived_liquidity,
            observed_possible_fill=observed_possible_fill,
            price_error_norm=price_error_norm,
            liquidity_error=liquidity_error,
            ledger_delay_error=ledger_delay_error,
            path_error=path_error,
            observation_confidence=observation_confidence,
            route_confidence=route_confidence,
            unique_routes_seen=unique_routes_seen,
            total_snapshots=total_snapshots,
        )
    )
    observation = XRPLBayesianObservation(
        observed_at=observed_at,
        sample_weight = max(0.25, observation_confidence),
        phantom_penalty=error_metrics.phantom_penalty,
        route_instability=error_metrics.route_instability,
        competition_penalty=error_metrics.competition_penalty,
        fill_disagreement=error_metrics.fill_disagreement,
        low_fill_bias=error_metrics.low_fill_bias,
        liquidity_error=liquidity_error,
        path_error=path_error,
        ledger_delay_error=ledger_delay_error,
        weighted_error=error_metrics.weighted_error,
    )
    return XRPLShadowCalibrationSample(
        execution_id=int(execution.id or 0),
        observed_possible_fill=round(observed_possible_fill, 6),
        snapshot_derived_liquidity=round(snapshot_derived_liquidity, 6),
        route_confidence=round(route_confidence, 6),
        route_used=route_used,
        observation_confidence=round(observation_confidence, 6),
        price_error_norm=round(price_error_norm, 6),
        liquidity_error=round(liquidity_error, 6),
        path_error=round(path_error, 6),
        ledger_delay_error=round(ledger_delay_error, 6),
        error_metrics=error_metrics,
        observation=observation,
    )


def build_xrpl_shadow_calibration_aggregate(
    *,
    executions: list[ExecutionRecord],
    orderbook_snapshots: list[XRPLOrderbookSnapshot],
    decay_half_life: float = 300.0,
) -> XRPLShadowCalibrationAggregate:
    snapshots_by_token: dict[int, list[XRPLOrderbookSnapshot]] = {}
    for row in orderbook_snapshots:
        snapshots_by_token.setdefault(int(row.token_id), []).append(row)
    for token_rows in snapshots_by_token.values():
        token_rows.sort(key=lambda row: int(row.ledger_index))

    samples: list[XRPLShadowCalibrationSample] = []
    model = XRPLShadowErrorModel()
    outcome_model = DecisionOutcomeModel()
    for execution in executions:
        if not _is_shadow_execution(execution):
            continue
        token_snapshots = snapshots_by_token.get(int(execution.token_id), [])
        low_ledger = min(int(execution.ledger_index_snapshot), int(execution.ledger_index_inclusion))
        high_ledger = max(int(execution.ledger_index_snapshot), int(execution.ledger_index_inclusion))
        sequence = [row for row in token_snapshots if low_ledger <= int(row.ledger_index) <= high_ledger][:64]
        sample = build_xrpl_shadow_calibration_sample(execution=execution, snapshots=sequence, error_model=model)
        outcome = build_decision_outcome_from_shadow_execution(execution)
        feedback = outcome_model.evaluate(outcome)
        sample.observation.sample_weight = max(
            0.25,
            sample.observation.sample_weight
            * (1.0 + feedback.weighted_error)
            * (1.0 + feedback.ledger_penalty)
            * (1.0 + feedback.route_penalty),
        )
        sample.observation.weighted_error = round(feedback.weighted_error, 6)
        sample.observation.ledger_delay_error = round(max(sample.observation.ledger_delay_error, feedback.ledger_penalty), 6)
        sample.observation.route_instability = round(max(sample.observation.route_instability, feedback.route_penalty), 6)
        sample.observation.competition_penalty = round(max(sample.observation.competition_penalty, feedback.competition_proxy), 6)
        samples.append(sample)

    observations = [row.observation for row in samples]
    phantom_penalty_avg = 0.0 if not samples else sum(row.error_metrics.phantom_penalty for row in samples) / len(samples)
    calibration = XRPLBayesianCalibrator(decay_half_life=decay_half_life).calibrate(
        observations,
        phantom_penalty_avg=phantom_penalty_avg,
    )

    if not samples:
        return XRPLShadowCalibrationAggregate(
            sample_count=0,
            shadow_disagreement_avg=0.0,
            phantom_liquidity_avg=0.0,
            phantom_penalty_avg=0.0,
            route_instability_avg=0.0,
            competition_failure_rate=0.0,
            fill_variance_avg=0.0,
            low_fill_bias_avg=0.0,
            price_error_norm_avg=0.0,
            liquidity_error_avg=0.0,
            ledger_delay_error_avg=0.0,
            path_error_avg=0.0,
            observation_confidence_avg=0.0,
            snapshot_derived_liquidity_avg=0.0,
            observed_possible_fill_avg=0.0,
            calibration=calibration,
            samples=[],
        )

    count = len(samples)
    return XRPLShadowCalibrationAggregate(
        sample_count=count,
        shadow_disagreement_avg=round(sum(row.error_metrics.weighted_error for row in samples) / count, 6),
        phantom_liquidity_avg=round(sum(row.error_metrics.phantom_liquidity for row in samples) / count, 6),
        phantom_penalty_avg=round(sum(row.error_metrics.phantom_penalty for row in samples) / count, 6),
        route_instability_avg=round(sum(row.error_metrics.route_instability for row in samples) / count, 6),
        competition_failure_rate=round(sum(row.error_metrics.competition_penalty for row in samples) / count, 6),
        fill_variance_avg=round(sum(row.error_metrics.fill_variance for row in samples) / count, 6),
        low_fill_bias_avg=round(sum(row.error_metrics.low_fill_bias for row in samples) / count, 6),
        price_error_norm_avg=round(sum(row.price_error_norm for row in samples) / count, 6),
        liquidity_error_avg=round(sum(row.liquidity_error for row in samples) / count, 6),
        ledger_delay_error_avg=round(sum(row.ledger_delay_error for row in samples) / count, 6),
        path_error_avg=round(sum(row.path_error for row in samples) / count, 6),
        observation_confidence_avg=round(sum(row.observation_confidence for row in samples) / count, 6),
        snapshot_derived_liquidity_avg=round(sum(row.snapshot_derived_liquidity for row in samples) / count, 6),
        observed_possible_fill_avg=round(sum(row.observed_possible_fill for row in samples) / count, 6),
        calibration=calibration,
        samples=samples,
    )