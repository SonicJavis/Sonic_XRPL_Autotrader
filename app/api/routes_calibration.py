from __future__ import annotations

from fastapi import APIRouter, Request
from sqlmodel import select

from app.calibration.fundedness_proxy import FundednessProxy
from app.calibration.regime_classifier import RegimeClassificationInput, XRPLRegimeClassifier
from app.calibration.temporal_comparison import compare_simulation_vs_sequence
from app.db.models import ExecutionRecord, XRPLOrderbookSequence, XRPLOrderbookSnapshot

router = APIRouter()


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
                "avg_decay_score": 0.0,
                "avg_volatility_score": 0.0,
                "collapse_events_total": 0,
            }

        results = []
        regimes: list[str] = []
        ledger_delay_errors: list[float] = []
        fundedness_proxy = FundednessProxy()
        regime_classifier = XRPLRegimeClassifier()
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
        "ledger_delay_error": round(ledger_delay_error, 6),
        "avg_decay_score": round(avg_decay, 6),
        "avg_volatility_score": round(avg_volatility, 6),
        "collapse_events_total": collapse_total,
    }