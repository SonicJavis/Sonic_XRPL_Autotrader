from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sqlmodel import select

from app.calibration.temporal_comparison import compare_simulation_vs_sequence
from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot
from app.validation.dual_error_engine import DualErrorEngine, DualErrorInput
from app.validation.execution_bounds import ExecutionBoundsInput, ExecutionBoundsModel
from app.validation.observation_uncertainty import ObservationSample, ObservationUncertaintyModel
from app.validation.report_engine import UncertaintyReportEngine, ValidationSample

router = APIRouter()

_VALIDATION_RUNS: list[dict[str, object]] = []


def _base_response_meta() -> dict[str, object]:
    return {
        "is_truth": False,
        "is_validation_only": True,
        "xrpl_warning": "Observed data may not reflect executable liquidity",
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
