from __future__ import annotations

import json
from math import isfinite

from fastapi import APIRouter, Request
from sqlmodel import select

from app.calibration.fundedness_proxy import FundednessProxy
from app.calibration.regime_classifier import RegimeClassificationInput, XRPLRegimeClassifier
from app.calibration.recommendation_engine import ConfidenceWeightedCalibrationEngine, LiveCalibrationSample
from app.calibration.temporal_comparison import compare_simulation_vs_sequence
from app.calibration.xrpl_bayesian_calibrator import build_xrpl_shadow_calibration_aggregate
from app.calibration.xrpl_time_execution_model import (
    XRPLTimeExecutionModel,
    build_time_execution_input_from_shadow_execution,
)
from app.db.models import ExecutionRecord, XRPLOrderbookSequence, XRPLOrderbookSnapshot

router = APIRouter()


def _shadow_calibration_meta() -> dict[str, object]:
    return {
        "is_advisory": True,
        "is_shadow": True,
        "is_shadow_calibration": True,
        "is_truth": False,
        "is_executable": False,
        "auto_apply": False,
        "requires_manual_review": True,
        "xrpl_warning": "Shadow calibration is advisory only and uses snapshot-derived liquidity under execution uncertainty",
    }


def _stats(values: list[float]) -> dict[str, float]:
    values = [float(value) for value in values if isfinite(float(value))]
    if not values:
        return {"min": 0.0, "max": 0.0, "avg": 0.0}
    return {
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "avg": round(sum(values) / len(values), 6),
    }


def _build_shadow_calibration(request: Request, *, limit: int = 500, snapshot_limit: int = 2000):
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 5000)
    safe_snapshot_limit = min(max(snapshot_limit, 1), 5000)
    with container.session_factory() as session:
        executions = session.exec(
            select(ExecutionRecord).order_by(ExecutionRecord.id.desc()).limit(safe_limit)
        ).all()
        snapshots = session.exec(
            select(XRPLOrderbookSnapshot).order_by(XRPLOrderbookSnapshot.ledger_index.asc()).limit(safe_snapshot_limit)
        ).all()
    return build_xrpl_shadow_calibration_aggregate(
        executions=executions,
        orderbook_snapshots=snapshots,
    )


@router.get("/calibration/gap-report")
def calibration_gap_report(request: Request, limit: int = 500) -> dict[str, object]:
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 5000)

    with container.session_factory() as session:
        executions = session.exec(
            select(ExecutionRecord).order_by(ExecutionRecord.id.desc()).limit(safe_limit)
        ).all()
        sequences = session.exec(
            select(XRPLOrderbookSequence).order_by(XRPLOrderbookSequence.id.desc()).limit(safe_limit)
        ).all()

        if not executions:
            return {
                "sample_size": 0,
                "sequence_count": len(sequences),
                "avg_execution_survivability_error": 0.0,
                "avg_slippage_underestimation": 0.0,
                "avg_depth_overestimation": 0.0,
                "avg_latency_miss_error": 0.0,
                "simulated_fail_in_real_rate": 0.0,
                "depth_illusion_rate": 0.0,
                "path_distortion_rate": 0.0,
                "fundedness_uncertainty_score": 1.0,
                "ledger_delay_error": 0.0,
                "live_simulated_fail_rate": 0.0,
                "path_mismatch_rate": 0.0,
                "avg_decay_score": 0.0,
                "avg_volatility_score": 0.0,
                "collapse_events_total": 0,
            }

        results = []
        regimes: list[str] = []
        ledger_delay_errors: list[float] = []
        live_samples: list[LiveCalibrationSample] = []
        fundedness_proxy = FundednessProxy()
        regime_classifier = XRPLRegimeClassifier()
        calibration_engine = ConfidenceWeightedCalibrationEngine()
        for row in executions:
            lower = min(int(row.ledger_index_snapshot), int(row.ledger_index_inclusion))
            upper = max(int(row.ledger_index_snapshot), int(row.ledger_index_inclusion))
            snapshots = session.exec(
                select(XRPLOrderbookSnapshot)
                .where(XRPLOrderbookSnapshot.token_id == row.token_id)
                .where(XRPLOrderbookSnapshot.ledger_index >= lower)
                .where(XRPLOrderbookSnapshot.ledger_index <= upper)
                .order_by(XRPLOrderbookSnapshot.ledger_index.asc())
                .limit(64)
            ).all()
            compared = compare_simulation_vs_sequence(execution=row, sequence=snapshots)
            results.append(compared)

            if snapshots:
                avg_depth = sum((float(s.bid_depth_xrp) + float(s.ask_depth_xrp)) for s in snapshots) / max(1, len(snapshots))
                visible_depth_score = max(0.0, min(1.0, avg_depth / 1200.0))
                seq_span = max(0, int(snapshots[-1].ledger_index) - int(snapshots[0].ledger_index))
            else:
                visible_depth_score = 0.0
                seq_span = 0

            expected_delay = max(0, int(row.ledger_index_inclusion) - int(row.ledger_index_snapshot))
            delay_error = abs(expected_delay - seq_span) / max(1.0, float(max(expected_delay, seq_span, 1)))
            ledger_delay_errors.append(max(0.0, min(1.0, delay_error)))

            seq_volatility = 0.0
            seq_decay = 0.0
            seq_collapse = 0
            if snapshots:
                matching = [
                    s
                    for s in sequences
                    if s.token_id == row.token_id and s.start_ledger <= lower and s.end_ledger >= upper
                ]
                if matching:
                    latest = matching[0]
                    seq_volatility = max(0.0, min(1.0, float(latest.volatility_score)))
                    seq_decay = max(0.0, min(1.0, float(latest.decay_score)))
                    seq_collapse = int(latest.collapse_events)

            classified = regime_classifier.classify(
                metrics=RegimeClassificationInput(
                    visible_depth_score=visible_depth_score,
                    execution_survivability_error=compared.execution_survivability_error,
                    slippage_underestimation=compared.slippage_underestimation,
                    depth_overestimation=compared.depth_overestimation,
                    volatility_score=seq_volatility,
                    decay_score=seq_decay,
                    wall_flicker_rate=1.0 if seq_collapse > 0 else 0.0,
                    inclusion_uncertainty=ledger_delay_errors[-1],
                )
            )
            regimes.append(classified.regime)

            try:
                details = json.loads(str(row.execution_details_json or "{}"))
            except json.JSONDecodeError:
                details = {}

            if bool(details.get("shadow")):
                simulated_fill_ratio = 0.0
                if float(row.requested_size or 0.0) > 0:
                    simulated_fill_ratio = max(0.0, min(1.0, float(row.filled_size or 0.0) / float(row.requested_size or 1.0)))

                observed_fill_ratio = max(
                    0.0,
                    min(1.0, float(details.get("observed_fill_ratio", max(0.0, 1.0 - compared.execution_survivability_error)))),
                )
                live_samples.append(
                    LiveCalibrationSample(
                        simulated_fill_ratio=simulated_fill_ratio,
                        observed_fill_ratio=observed_fill_ratio,
                        disagreement_score=max(0.0, min(1.0, float(details.get("disagreement_score", compared.depth_overestimation)))),
                        ledger_delay_error=max(0.0, min(1.0, float(details.get("ledger_delay_error", ledger_delay_errors[-1])))),
                        path_execution_risk=max(0.0, min(1.0, float(details.get("path_execution_risk", 0.0)))),
                        observation_confidence=max(0.0, min(1.0, float(details.get("observation_confidence", 0.5)))),
                    )
                )

        fundedness_confidence = fundedness_proxy.evaluate(
            sorted(
                session.exec(select(XRPLOrderbookSnapshot).order_by(XRPLOrderbookSnapshot.ledger_index.asc()).limit(300)).all(),
                key=lambda s: s.ledger_index,
            )
        ).fundedness_confidence

    total = len(results)
    avg_survivability = sum(r.execution_survivability_error for r in results) / max(1, total)
    avg_slippage = sum(r.slippage_underestimation for r in results) / max(1, total)
    avg_depth = sum(r.depth_overestimation for r in results) / max(1, total)
    avg_latency = sum(r.latency_miss_error for r in results) / max(1, total)

    # Conservative proxy: count executions likely to fail in real conditions.
    simulated_fail_in_real = sum(1 for r in results if r.execution_survivability_error >= 0.25) / max(1, total)
    depth_illusion_rate = sum(1 for r in regimes if r == "ILLUSION_LIQUIDITY") / max(1, len(regimes))
    path_distortion_rate = sum(1 for r in regimes if r == "PATH_DISTORTED") / max(1, len(regimes))
    fundedness_uncertainty_score = 1.0 - max(0.0, min(1.0, fundedness_confidence))
    ledger_delay_error = 0.0 if not ledger_delay_errors else (sum(ledger_delay_errors) / len(ledger_delay_errors))
    live_summary = calibration_engine.summarize_live_metrics(live_samples)

    seq_count = len(sequences)
    avg_decay = 0.0 if seq_count == 0 else sum(float(s.decay_score) for s in sequences) / seq_count
    avg_volatility = 0.0 if seq_count == 0 else sum(float(s.volatility_score) for s in sequences) / seq_count
    collapse_total = 0 if seq_count == 0 else sum(int(s.collapse_events) for s in sequences)

    return {
        "sample_size": total,
        "sequence_count": seq_count,
        "avg_execution_survivability_error": round(avg_survivability, 6),
        "avg_slippage_underestimation": round(avg_slippage, 6),
        "avg_depth_overestimation": round(avg_depth, 6),
        "avg_latency_miss_error": round(avg_latency, 6),
        "simulated_fail_in_real_rate": round(simulated_fail_in_real, 6),
        "depth_illusion_rate": round(depth_illusion_rate, 6),
        "path_distortion_rate": round(path_distortion_rate, 6),
        "fundedness_uncertainty_score": round(fundedness_uncertainty_score, 6),
        "ledger_delay_error": round(max(ledger_delay_error, live_summary.ledger_delay_error), 6),
        "live_simulated_fail_rate": live_summary.live_simulated_fail_rate,
        "path_mismatch_rate": live_summary.path_mismatch_rate,
        "avg_decay_score": round(avg_decay, 6),
        "avg_volatility_score": round(avg_volatility, 6),
        "collapse_events_total": collapse_total,
    }


@router.get("/calibration/shadow/xrpl/errors")
def calibration_shadow_xrpl_errors(request: Request, limit: int = 500) -> dict[str, object]:
    aggregate = _build_shadow_calibration(request, limit=limit)
    return {
        **_shadow_calibration_meta(),
        "sample_count": aggregate.sample_count,
        "errors": {
            "shadow_disagreement_avg": aggregate.shadow_disagreement_avg,
            "phantom_liquidity_avg": aggregate.phantom_liquidity_avg,
            "phantom_penalty_avg": aggregate.phantom_penalty_avg,
            "route_instability_avg": aggregate.route_instability_avg,
            "competition_failure_rate": aggregate.competition_failure_rate,
            "fill_variance_avg": aggregate.fill_variance_avg,
            "low_fill_bias_avg": aggregate.low_fill_bias_avg,
            "price_error_norm_avg": aggregate.price_error_norm_avg,
            "liquidity_error_avg": aggregate.liquidity_error_avg,
            "ledger_delay_error_avg": aggregate.ledger_delay_error_avg,
            "path_error_avg": aggregate.path_error_avg,
            "observation_confidence_avg": aggregate.observation_confidence_avg,
            "snapshot_derived_liquidity_avg": aggregate.snapshot_derived_liquidity_avg,
            "observed_possible_fill_avg": aggregate.observed_possible_fill_avg,
        },
    }


@router.get("/calibration/shadow/xrpl/reliability")
def calibration_shadow_xrpl_reliability(request: Request, limit: int = 500) -> dict[str, object]:
    aggregate = _build_shadow_calibration(request, limit=limit)
    calibration = aggregate.calibration
    return {
        **_shadow_calibration_meta(),
        "sample_count": aggregate.sample_count,
        "decay_half_life_seconds": calibration.decay_half_life,
        "reliability_lower_bounds": {
            "liquidity_reliability": calibration.liquidity_reliability.lower_bound,
            "path_reliability": calibration.path_reliability.lower_bound,
            "latency_reliability": calibration.latency_reliability.lower_bound,
            "fill_reliability": calibration.fill_reliability.lower_bound,
            "competition_reliability": calibration.competition_reliability.lower_bound,
            "drift_reliability": calibration.drift_reliability.lower_bound,
            "latency_stability": calibration.latency_stability.lower_bound,
            "path_reliability_weighting": calibration.path_reliability_weighting.lower_bound,
        },
        "adaptive_weights": {
            "liquidity_reliability": calibration.liquidity_reliability.adaptive_weight,
            "path_reliability": calibration.path_reliability.adaptive_weight,
            "latency_reliability": calibration.latency_reliability.adaptive_weight,
            "fill_reliability": calibration.fill_reliability.adaptive_weight,
            "competition_reliability": calibration.competition_reliability.adaptive_weight,
            "drift_reliability": calibration.drift_reliability.adaptive_weight,
            "latency_stability": calibration.latency_stability.adaptive_weight,
            "path_reliability_weighting": calibration.path_reliability_weighting.adaptive_weight,
        },
    }


@router.get("/calibration/shadow/xrpl/time-model")
def calibration_shadow_xrpl_time_model(request: Request, limit: int = 500) -> dict[str, object]:
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 5000)
    with container.session_factory() as session:
        executions = session.exec(
            select(ExecutionRecord).order_by(ExecutionRecord.id.desc()).limit(safe_limit)
        ).all()

    model = XRPLTimeExecutionModel()
    latency_values: list[float] = []
    drift_values: list[float] = []
    path_complexities: list[float] = []
    fill_values: list[float] = []
    decay_values: list[float] = []
    ev_before_values: list[float] = []
    ev_after_values: list[float] = []
    sample_rows: list[dict[str, float | int]] = []

    for execution in executions:
        try:
            details = json.loads(str(execution.execution_details_json or "{}"))
        except json.JSONDecodeError:
            details = {}
        if not bool(details.get("shadow")):
            continue

        data = build_time_execution_input_from_shadow_execution(execution, details)
        result = model.evaluate(data)
        base_probability = max(0.0, min(1.0, float(data.base_fill_probability)))
        ev_before_drift = base_probability * (1.0 - max(0.0, float(data.slippage_estimate))) - (1.0 - base_probability)

        latency_values.append(result.latency_seconds)
        drift_values.append(result.price_drift)
        path_complexities.append(float(data.path_complexity))
        fill_values.append(result.effective_fill_probability)
        decay_values.append(result.liquidity_decay)
        ev_before_values.append(round(ev_before_drift, 6))
        ev_after_values.append(result.drift_adjusted_ev)
        sample_rows.append(
            {
                "execution_id": int(execution.id or 0),
                "latency_seconds": result.latency_seconds,
                "ledger_delay": result.ledger_delay,
                "price_drift": result.price_drift,
                "path_complexity": int(data.path_complexity),
                "liquidity_decay": result.liquidity_decay,
                "effective_fill_probability": result.effective_fill_probability,
                "ev_before_drift": round(ev_before_drift, 6),
                "drift_adjusted_ev": result.drift_adjusted_ev,
            }
        )

    return {
        **_shadow_calibration_meta(),
        "sample_count": len(sample_rows),
        "latency_distribution": latency_values,
        "drift_distribution": drift_values,
        "path_complexity_stats": _stats(path_complexities),
        "decay_stats": _stats(decay_values),
        "fill_probability_stats": _stats(fill_values),
        "ev_before_drift_stats": _stats(ev_before_values),
        "drift_adjusted_ev_stats": _stats(ev_after_values),
        "samples": sample_rows[:100],
    }


@router.get("/calibration/shadow/xrpl/recommendations")
def calibration_shadow_xrpl_recommendations(request: Request, limit: int = 500) -> dict[str, object]:
    aggregate = _build_shadow_calibration(request, limit=limit)
    recommendations = aggregate.calibration.recommendations
    return {
        **_shadow_calibration_meta(),
        "sample_count": aggregate.sample_count,
        "recommendations": {
            "liquidity_haircut": recommendations.liquidity_haircut,
            "expected_slippage_multiplier": recommendations.expected_slippage_multiplier,
            "execution_probability_floor": recommendations.execution_probability_floor,
            "competition_risk_multiplier": recommendations.competition_risk_multiplier,
        },
    }
