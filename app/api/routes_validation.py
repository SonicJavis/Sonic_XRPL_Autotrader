from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlmodel import select

from app.calibration.temporal_comparison import compare_simulation_vs_sequence
from app.db.models import CalibrationReviewRecord, ExecutionRecord, ShadowValidationRecord, WatchedToken, XRPLOrderbookSnapshot
from app.validation.dual_error_engine import DualErrorEngine, DualErrorInput
from app.validation.execution_bounds import ExecutionBoundsInput, ExecutionBoundsModel
from app.validation.observation_uncertainty import ObservationSample, ObservationUncertaintyModel
from app.validation.report_engine import UncertaintyReportEngine, ValidationSample
from app.validation.xrpl_calibration_review import (
    REVIEW_DECISIONS,
    REVIEW_SCHEMA_VERSION,
    REVIEW_WARNING,
    build_audit_export_bundle,
    build_review_record,
    filter_review_rows,
    review_to_dict,
)
from app.validation.xrpl_calibration_recommendations import (
    RECOMMENDATION_SCHEMA_VERSION,
    XRPL_CALIBRATION_WARNING,
    XRPLCalibrationRecommendationEngine,
)
from app.validation.xrpl_order_intents import (
    ORDER_INTENT_SCHEMA_VERSION,
    XRPL_ORDER_INTENT_WARNING,
    XRPLIntentSnapshot,
    build_order_intents,
    summarize_order_intents,
)
from app.live.xrpl_live_shadow_pipeline import default_live_drift, default_live_metrics, default_live_status

router = APIRouter()

_VALIDATION_RUNS: list[dict[str, object]] = []


class CalibrationReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation: dict[str, object]
    decision: str
    review_notes: str = ""
    reviewer_id: str | None = None
    reviewed_at: datetime


def _base_response_meta() -> dict[str, object]:
    return {
        "is_truth": False,
        "is_validation_only": True,
        "xrpl_warning": "Observed data may not reflect executable liquidity",
    }


def _shadow_meta() -> dict[str, object]:
    return {
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": "No ground truth exists; observed outcomes are probabilistic and validation measures observed disagreement under uncertainty",
    }


def _safe_limit(raw: int) -> int:
    return min(max(int(raw), 1), 5000)


def _finite(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return value if value == value and value not in (float("inf"), float("-inf")) else 0.0


def _record_to_dict(row: ShadowValidationRecord) -> dict[str, object]:
    return {
        "id": int(row.id or 0),
        "decision_id": int(row.decision_id),
        "token_id": int(row.token_id),
        "issuer": row.issuer,
        "predicted_regime": row.predicted_regime,
        "fill_probability_error": _finite(row.fill_probability_error),
        "effective_size_error": _finite(row.effective_size_error),
        "ev_error": _finite(row.ev_error),
        "liquidity_disappearance": _finite(row.liquidity_disappearance),
        "path_failure_rate": _finite(row.path_failure_rate),
        "competition_miss_rate": _finite(row.competition_miss_rate),
        "latency_miss": _finite(row.latency_miss),
        "regime_mismatch": bool(row.regime_mismatch),
        "disagreement_score": _finite(row.disagreement_score),
        "brier_score": _finite(row.brier_score),
        "overconfidence_flag": bool(row.overconfidence_flag),
        "underconfidence_flag": bool(row.underconfidence_flag),
        "confidence_error": _finite(row.confidence_error),
        "attribution": row.attribution,
        "created_at": row.created_at.astimezone(timezone.utc).isoformat(),
        "is_shadow": bool(row.is_shadow),
        "is_advisory": bool(row.is_advisory),
        "is_executable": bool(row.is_executable),
        "is_truth": bool(row.is_truth),
    }


def _build_uncertainty_report(request: Request, limit: int) -> dict[str, object]:
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 2000)

    samples: list[ValidationSample] = []
    with container.session_factory() as session:
        executions = session.exec(
            select(ExecutionRecord).order_by(ExecutionRecord.id.desc()).limit(safe_limit)
        ).all()
        for row in executions:
            low_ledger = min(int(row.ledger_index_snapshot), int(row.ledger_index_inclusion))
            high_ledger = max(int(row.ledger_index_snapshot), int(row.ledger_index_inclusion))
            snaps = session.exec(
                select(XRPLOrderbookSnapshot)
                .where(XRPLOrderbookSnapshot.token_id == row.token_id)
                .where(XRPLOrderbookSnapshot.ledger_index >= low_ledger)
                .where(XRPLOrderbookSnapshot.ledger_index <= high_ledger)
                .order_by(XRPLOrderbookSnapshot.ledger_index.asc())
                .limit(64)
            ).all()

            temporal = compare_simulation_vs_sequence(execution=row, sequence=snaps)
            obs_samples = [
                ObservationSample(
                    bid_depth_xrp=float(s.bid_depth_xrp),
                    ask_depth_xrp=float(s.ask_depth_xrp),
                    spread_pct=float(s.spread_pct),
                    best_bid=float(s.best_bid),
                    best_ask=float(s.best_ask),
                    implied_mid_price=(float(s.best_bid) + float(s.best_ask)) / 2.0,
                )
                for s in snaps
            ]
            obs = ObservationUncertaintyModel().evaluate(obs_samples)

            bounds = ExecutionBoundsModel().compute(
                data=ExecutionBoundsInput(
                    total_visible_depth_xrp=sum(float(s.ask_depth_xrp) for s in snaps),
                    requested_size_xrp=float(row.requested_size or 0.0),
                    depth_uncertainty=max(0.0, min(1.0, 1.0 - obs.depth_reliability_score)),
                    fundedness_uncertainty=obs.fundedness_uncertainty,
                    decay_rate=temporal.depth_overestimation,
                    regime="UNKNOWN",
                ),
                simulator_fill_size_xrp=float(row.filled_size or 0.0),
            )

            dual = DualErrorEngine().evaluate(
                DualErrorInput(
                    simulator_fillable=float(row.filled_size or 0.0) > 0.0,
                    simulator_fill_ratio=(
                        0.0
                        if float(row.requested_size or 0.0) <= 0
                        else min(1.0, float(row.filled_size or 0.0) / float(row.requested_size or 1.0))
                    ),
                    observed_depth_present=bool(snaps and any(float(s.ask_depth_xrp) > 0 for s in snaps)),
                    observation_confidence=obs.observation_confidence,
                    observed_fill_probability=bounds.fill_probability_range[1],
                )
            )

            samples.append(
                ValidationSample(
                    token_key=f"token:{row.token_id}",
                    disagreement_score=dual.disagreement_score,
                    false_confidence_flag=dual.false_confidence_flag,
                    observation_confidence=obs.observation_confidence,
                    simulator_within_bounds=bounds.simulator_within_bounds,
                )
            )

    report = UncertaintyReportEngine().build(samples)
    return {
        **_base_response_meta(),
        "report": {
            "disagreement_score": report.disagreement_score,
            "false_confidence_rate": report.false_confidence_rate,
            "observation_confidence_avg": report.observation_confidence_avg,
            "simulator_within_bounds_rate": report.simulator_within_bounds_rate,
            "worst_tokens": report.worst_tokens,
            "recommendation": report.recommendation,
        },
        "sample_size": len(samples),
    }


@router.get("/validation/uncertainty-report")
def validation_uncertainty_report(request: Request, limit: int = 300) -> dict[str, object]:
    return _build_uncertainty_report(request, limit=limit)


@router.get("/validation/runs")
def validation_runs() -> dict[str, object]:
    return {**_base_response_meta(), "runs": list(_VALIDATION_RUNS)}


@router.post("/validation/from-calibration")
def validation_from_calibration(request: Request, limit: int = 300) -> dict[str, object]:
    generated = _build_uncertainty_report(request, limit=limit)
    run = {
        "run_id": len(_VALIDATION_RUNS) + 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sample_size": generated.get("sample_size", 0),
        "disagreement_score": generated.get("report", {}).get("disagreement_score", 1.0),
        "recommendation": generated.get("report", {}).get("recommendation", "COLLECT_MORE_DATA"),
    }
    _VALIDATION_RUNS.append(run)

    return {**_base_response_meta(), "run": run, "report": generated.get("report", {})}


@router.get("/validation/shadow/results")
def validation_shadow_results(request: Request, limit: int = 200) -> dict[str, object]:
    safe_limit = _safe_limit(limit)
    with request.app.state.container.session_factory() as session:
        rows = session.exec(
            select(ShadowValidationRecord).order_by(ShadowValidationRecord.created_at.desc(), ShadowValidationRecord.id.desc()).limit(safe_limit)
        ).all()
    return {
        **_shadow_meta(),
        "limit": safe_limit,
        "count": len(rows),
        "results": [_record_to_dict(row) for row in rows],
    }


@router.get("/validation/shadow/summary")
def validation_shadow_summary(request: Request, limit: int = 500) -> dict[str, object]:
    safe_limit = _safe_limit(limit)
    with request.app.state.container.session_factory() as session:
        rows = session.exec(
            select(ShadowValidationRecord).order_by(ShadowValidationRecord.created_at.desc(), ShadowValidationRecord.id.desc()).limit(safe_limit)
        ).all()
    count = len(rows)
    attribution: dict[str, int] = {}
    regime_scores: dict[str, list[float]] = {}
    token_scores: dict[str, list[float]] = {}
    for row in rows:
        attribution[row.attribution] = attribution.get(row.attribution, 0) + 1
        regime_scores.setdefault(row.predicted_regime, []).append(_finite(row.disagreement_score))
        token_scores.setdefault(str(row.token_id), []).append(_finite(row.disagreement_score))
    return {
        **_shadow_meta(),
        "limit": safe_limit,
        "sample_count": count,
        "avg_disagreement_score": 0.0 if count == 0 else round(sum(_finite(row.disagreement_score) for row in rows) / count, 6),
        "avg_brier_score": 0.0 if count == 0 else round(sum(_finite(row.brier_score) for row in rows) / count, 6),
        "overconfidence_rate": 0.0 if count == 0 else round(sum(1 for row in rows if row.overconfidence_flag) / count, 6),
        "underconfidence_rate": 0.0 if count == 0 else round(sum(1 for row in rows if row.underconfidence_flag) / count, 6),
        "attribution_breakdown": dict(sorted(attribution.items())),
        "worst_regimes": _worst(regime_scores),
        "worst_tokens": _worst(token_scores),
    }


@router.get("/validation/calibration/recommendations")
def validation_calibration_recommendations(request: Request, limit: int = 5000, min_support: int = 30) -> dict[str, object]:
    safe_limit = _safe_limit(limit)
    min_support = max(30, int(min_support))
    with request.app.state.container.session_factory() as session:
        rows = session.exec(
            select(ShadowValidationRecord).order_by(ShadowValidationRecord.created_at.desc(), ShadowValidationRecord.id.desc()).limit(safe_limit)
        ).all()
    recommendations = XRPLCalibrationRecommendationEngine().generate(rows, min_support=min_support)[:safe_limit]
    return {
        "schema_version": RECOMMENDATION_SCHEMA_VERSION,
        "limit": safe_limit,
        "min_support": min_support,
        "effective_sample_size": len(rows),
        "count": len(recommendations),
        "recommendations": [row.to_dict() for row in recommendations],
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": XRPL_CALIBRATION_WARNING,
        "low_sample_warning": len(rows) < min_support,
    }


@router.post("/validation/calibration/review")
def validation_calibration_review(request: Request, payload: CalibrationReviewRequest) -> dict[str, object]:
    try:
        review = build_review_record(
            recommendation=payload.recommendation,
            decision=payload.decision,
            review_notes=payload.review_notes,
            reviewer_id=payload.reviewer_id,
            reviewed_at=payload.reviewed_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    with request.app.state.container.session_factory() as session:
        session.add(review)
        session.commit()
        session.refresh(review)
        body = review_to_dict(review)
    return {
        **_review_meta(),
        "review": body,
        "decision_meanings": _decision_meanings(),
    }


@router.get("/validation/calibration/reviews")
def validation_calibration_reviews(
    request: Request,
    limit: int = 500,
    decision: str | None = None,
    recommendation_id: str | None = None,
    attribution: str | None = None,
    regime: str | None = None,
    token_id: int | None = None,
    issuer: str | None = None,
) -> dict[str, object]:
    safe_limit = _safe_limit(limit)
    safe_decision = decision.strip().lower() if decision else None
    if safe_decision is not None and safe_decision not in REVIEW_DECISIONS:
        raise HTTPException(status_code=400, detail="decision must be accepted, rejected, deferred, or noted")
    with request.app.state.container.session_factory() as session:
        rows = session.exec(
            select(CalibrationReviewRecord)
            .order_by(CalibrationReviewRecord.reviewed_at.desc(), CalibrationReviewRecord.id.desc())
            .limit(5000)
        ).all()
    filtered = filter_review_rows(
        rows,
        decision=safe_decision,
        recommendation_id=recommendation_id,
        attribution=attribution,
        regime=regime,
        token_id=token_id,
        issuer=issuer,
    )[:safe_limit]
    return {
        **_review_meta(),
        "schema_version": REVIEW_SCHEMA_VERSION,
        "limit": safe_limit,
        "count": len(filtered),
        "reviews": [review_to_dict(row) for row in filtered],
        "decision_meanings": _decision_meanings(),
    }


@router.get("/validation/calibration/export")
def validation_calibration_export(
    request: Request,
    limit: int = 5000,
    min_support: int = 30,
    deterministic: bool = False,
) -> dict[str, object]:
    safe_limit = _safe_limit(limit)
    min_support = max(30, int(min_support))
    with request.app.state.container.session_factory() as session:
        validation_rows = session.exec(
            select(ShadowValidationRecord)
            .order_by(ShadowValidationRecord.created_at.desc(), ShadowValidationRecord.id.desc())
            .limit(safe_limit)
        ).all()
        review_rows = session.exec(
            select(CalibrationReviewRecord)
            .order_by(CalibrationReviewRecord.reviewed_at.desc(), CalibrationReviewRecord.id.desc())
            .limit(safe_limit)
        ).all()
    recommendations = [
        row.to_dict()
        for row in XRPLCalibrationRecommendationEngine().generate(validation_rows, min_support=min_support)[:safe_limit]
    ]
    return build_audit_export_bundle(
        recommendations=recommendations,
        reviews=review_rows,
        deterministic=deterministic,
    )


@router.get("/validation/intents")
def validation_intents(request: Request, limit: int = 500, requested_size: float = 100.0) -> dict[str, object]:
    safe_limit = _safe_limit(limit)
    intents = _build_intents(request, limit=safe_limit, requested_size=requested_size)
    return {
        **_intent_meta(),
        "schema_version": ORDER_INTENT_SCHEMA_VERSION,
        "limit": safe_limit,
        "count": len(intents),
        "intents": [intent.to_dict() for intent in intents[:safe_limit]],
    }


@router.get("/validation/intents/summary")
def validation_intents_summary(request: Request, limit: int = 500, requested_size: float = 100.0) -> dict[str, object]:
    safe_limit = _safe_limit(limit)
    intents = _build_intents(request, limit=safe_limit, requested_size=requested_size)
    return {
        **_intent_meta(),
        "limit": safe_limit,
        "summary": summarize_order_intents(intents[:safe_limit]),
    }


@router.get("/validation/intents/{intent_id}")
def validation_intent_detail(request: Request, intent_id: str, limit: int = 500, requested_size: float = 100.0) -> dict[str, object]:
    safe_limit = _safe_limit(limit)
    intents = _build_intents(request, limit=safe_limit, requested_size=requested_size)
    for intent in intents:
        body = intent.to_dict()
        if body["intent_id"] == intent_id:
            return {**_intent_meta(), "intent": body}
    raise HTTPException(status_code=404, detail="intent not found")


@router.get("/validation/live/status")
def validation_live_status(request: Request) -> dict[str, object]:
    pipeline = getattr(request.app.state, "live_shadow_pipeline", None)
    if pipeline is None:
        return default_live_status()
    return pipeline.status()


@router.get("/validation/live/metrics")
def validation_live_metrics(request: Request) -> dict[str, object]:
    pipeline = getattr(request.app.state, "live_shadow_pipeline", None)
    if pipeline is None:
        return default_live_metrics()
    return pipeline.metrics_body()


@router.get("/validation/live/drift")
def validation_live_drift(request: Request) -> dict[str, object]:
    pipeline = getattr(request.app.state, "live_shadow_pipeline", None)
    if pipeline is None:
        return default_live_drift()
    return pipeline.drift()


def _build_intents(request: Request, *, limit: int, requested_size: float) -> list:
    with request.app.state.container.session_factory() as session:
        validation_rows = session.exec(
            select(ShadowValidationRecord).order_by(ShadowValidationRecord.created_at.desc(), ShadowValidationRecord.id.desc()).limit(limit)
        ).all()
        recommendations = [
            row.to_dict()
            for row in XRPLCalibrationRecommendationEngine().generate(validation_rows, min_support=1)[:limit]
        ]
        token_rows = session.exec(select(WatchedToken)).all()
        token_meta = {
            int(row.id): row
            for row in token_rows
            if row.id is not None
        }
        latest_snapshots = session.exec(
            select(XRPLOrderbookSnapshot).order_by(XRPLOrderbookSnapshot.ledger_index.desc(), XRPLOrderbookSnapshot.id.desc()).limit(5000)
        ).all()
    snapshots_by_token: dict[int, XRPLIntentSnapshot] = {}
    for snapshot in latest_snapshots:
        token_id = int(snapshot.token_id)
        if token_id in snapshots_by_token:
            continue
        token = token_meta.get(token_id)
        snapshots_by_token[token_id] = XRPLIntentSnapshot.from_row(
            snapshot,
            issuer="" if token is None else token.issuer,
            currency="" if token is None else token.currency,
        )
    return build_order_intents(
        recommendations=recommendations,
        snapshots_by_token=snapshots_by_token,
        requested_size=max(0.0, _finite(requested_size)),
    )


def _worst(groups: dict[str, list[float]]) -> list[dict[str, object]]:
    rows = [
        {"key": key, "avg_disagreement_score": round(sum(values) / max(len(values), 1), 6), "sample_count": len(values)}
        for key, values in groups.items()
    ]
    return sorted(rows, key=lambda item: (-float(item["avg_disagreement_score"]), str(item["key"])))[:10]


def _review_meta() -> dict[str, object]:
    return {
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": REVIEW_WARNING,
    }


def _intent_meta() -> dict[str, object]:
    return {
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": XRPL_ORDER_INTENT_WARNING,
    }


def _decision_meanings() -> dict[str, str]:
    return {
        "accepted": "human marked this for manual consideration only",
        "rejected": "human disagreed with the recommendation framing",
        "deferred": "human requested more evidence before consideration",
        "noted": "informational review record only",
    }
