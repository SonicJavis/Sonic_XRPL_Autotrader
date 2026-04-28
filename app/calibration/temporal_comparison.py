from __future__ import annotations

from dataclasses import dataclass

from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot


@dataclass(slots=True)
class TemporalComparisonResult:
    execution_survivability_error: float
    slippage_underestimation: float
    depth_overestimation: float
    latency_miss_error: float


def compare_simulation_vs_sequence(
    *,
    execution: ExecutionRecord,
    sequence: list[XRPLOrderbookSnapshot],
) -> TemporalComparisonResult:
    if not sequence:
        return TemporalComparisonResult(
            execution_survivability_error=1.0,
            slippage_underestimation=1.0,
            depth_overestimation=1.0,
            latency_miss_error=1.0,
        )

    ordered = sorted(sequence, key=lambda s: s.ledger_index)
    sim_requested = max(0.0, float(execution.requested_size or 0.0))
    sim_filled = max(0.0, float(execution.filled_size or 0.0))
    sim_fill_ratio = 0.0 if sim_requested <= 0 else min(1.0, sim_filled / sim_requested)

    worst_depth = min(max(0.0, float(s.ask_depth_xrp)) for s in ordered)
    avg_spread = sum(max(0.0, float(s.spread_pct)) for s in ordered) / max(1, len(ordered))

    survival_fillable = min(sim_requested, worst_depth)
    real_fill_ratio = 0.0 if sim_requested <= 0 else min(1.0, survival_fillable / sim_requested)
    execution_survivability_error = max(0.0, min(1.0, sim_fill_ratio - real_fill_ratio))

    spread_slippage_proxy = avg_spread / 2.0
    sim_slippage = max(0.0, float(execution.slippage_vs_top or 0.0))
    slippage_underestimation = max(0.0, min(1.0, (spread_slippage_proxy - sim_slippage) / 10.0))

    first_depth = max(0.0, float(ordered[0].ask_depth_xrp))
    depth_overestimation = 0.0
    if first_depth > 0:
        depth_overestimation = max(0.0, min(1.0, (first_depth - worst_depth) / first_depth))

    ledger_span = max(0, int(ordered[-1].ledger_index) - int(ordered[0].ledger_index))
    latency_ledgers = max(0, int(execution.ledger_index_inclusion) - int(execution.ledger_index_snapshot))
    latency_miss_error = max(0.0, min(1.0, abs(latency_ledgers - ledger_span) / max(1.0, float(max(latency_ledgers, ledger_span, 1)))))

    return TemporalComparisonResult(
        execution_survivability_error=execution_survivability_error,
        slippage_underestimation=slippage_underestimation,
        depth_overestimation=depth_overestimation,
        latency_miss_error=latency_miss_error,
    )
