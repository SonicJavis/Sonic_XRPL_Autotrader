from __future__ import annotations

from fastapi import APIRouter, Request
from sqlmodel import select

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
                "avg_decay_score": 0.0,
                "avg_volatility_score": 0.0,
                "collapse_events_total": 0,
            }

        results = []
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
            results.append(compare_simulation_vs_sequence(execution=row, sequence=snapshots))

    total = len(results)
    avg_survivability = sum(r.execution_survivability_error for r in results) / max(1, total)
    avg_slippage = sum(r.slippage_underestimation for r in results) / max(1, total)
    avg_depth = sum(r.depth_overestimation for r in results) / max(1, total)
    avg_latency = sum(r.latency_miss_error for r in results) / max(1, total)

    # Conservative proxy: count executions likely to fail in real conditions.
    simulated_fail_in_real = sum(1 for r in results if r.execution_survivability_error >= 0.25) / max(1, total)

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
        "avg_decay_score": round(avg_decay, 6),
        "avg_volatility_score": round(avg_volatility, 6),
        "collapse_events_total": collapse_total,
    }