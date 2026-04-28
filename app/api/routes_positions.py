from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from app.db.models import ExecutionRecord, MarketSnapshot, Position
from app.execution.pnl_attribution_engine import PnLAttributionEngine

router = APIRouter()


@router.get("/positions")
def list_positions(request: Request, limit: int = 200) -> list[dict[str, object]]:
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 500)
    with container.session_factory() as session:
        rows = session.exec(select(Position).order_by(Position.entry_time.desc()).limit(safe_limit)).all()
    return [row.model_dump() for row in rows]


@router.get("/positions/{position_id}")
def get_position(position_id: str, request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        row = session.get(Position, position_id)
    if row is None:
        raise HTTPException(status_code=404, detail="position not found")
    return row.model_dump()


@router.get("/pnl/realized")
def pnl_realized(request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PnLAttributionEngine()
        return engine.realized_pnl_summary(session)


@router.get("/pnl/unrealized")
def pnl_unrealized(request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PnLAttributionEngine()
        return engine.unrealized_pnl_summary(
            session,
            execution_latency_ms=container.settings.EXECUTION_LATENCY_MS,
            max_snapshot_age_ms=container.settings.MAX_SNAPSHOT_AGE_MS,
            liquidity_haircut_pct=container.settings.EXECUTION_LIQUIDITY_HAIRCUT_PCT,
            snapshot_to_decision_ms=container.settings.SNAPSHOT_TO_DECISION_MS,
            decision_to_submission_ms=container.settings.DECISION_TO_SUBMISSION_MS,
            submission_to_inclusion_ms=container.settings.SUBMISSION_TO_INCLUSION_MS,
            latency_haircut_pct=container.settings.EXECUTION_LATENCY_HAIRCUT_PCT,
            contention_haircut_pct=container.settings.EXECUTION_CONTENTION_HAIRCUT_PCT,
            trustline_liquidity_discount_pct=container.settings.EXECUTION_TRUSTLINE_DISCOUNT_PCT,
            ledger_drift_pct=container.settings.EXECUTION_LEDGER_DRIFT_PCT,
        )


@router.get("/failures")
def list_failures(request: Request, limit: int = 200) -> list[dict[str, object]]:
    container = request.app.state.container
    with container.session_factory() as session:
        engine = PnLAttributionEngine()
        return engine.list_failures(session, limit=limit)


@router.get("/execution/quality")
def execution_quality(request: Request, limit: int = 500) -> dict[str, object]:
    container = request.app.state.container
    safe_limit = min(max(limit, 1), 2000)

    with container.session_factory() as session:
        rows = session.exec(select(ExecutionRecord).order_by(ExecutionRecord.id.desc()).limit(safe_limit)).all()

    total = len(rows)
    if total == 0:
        return {
            "sample_size": 0,
            "fill_efficiency": 0.0,
            "avg_levels_consumed": 0.0,
            "levels_consumed_avg": 0.0,
            "queue_impact_pct": 0.0,
            "effective_vs_raw_liquidity": 0.0,
            "partial_fill_rate": 0.0,
            "avg_snapshot_age_ms": 0.0,
            "avg_execution_latency_ms": 0.0,
            "avg_snapshot_to_decision_ms": 0.0,
            "avg_decision_to_submission_ms": 0.0,
            "avg_submission_to_inclusion_ms": 0.0,
            "avg_slippage_vs_top": 0.0,
            "failure_rate_by_reason": {},
        }

    requested_sum = sum(max(0.0, float(r.requested_size or 0.0)) for r in rows)
    filled_sum = sum(max(0.0, float(r.filled_size or 0.0)) for r in rows)
    fill_efficiency = 0.0 if requested_sum <= 0 else filled_sum / requested_sum

    levels_consumed = [len(list(r.fill_levels_json or [])) for r in rows]
    avg_levels_consumed = sum(levels_consumed) / max(1, len(levels_consumed))

    queue_impacts: list[float] = []
    for row in rows:
        for level in list(row.fill_levels_json or []):
            raw_liq = float(level.get("raw_liquidity_xrp", 0.0) or 0.0)
            eff_liq = float(level.get("effective_liquidity_xrp", 0.0) or 0.0)
            if raw_liq > 0:
                queue_impacts.append(max(0.0, min(1.0, (raw_liq - eff_liq) / raw_liq)))
    queue_impact_pct = 0.0 if not queue_impacts else (sum(queue_impacts) / len(queue_impacts)) * 100.0
    effective_vs_raw_liquidity = 1.0 - (queue_impact_pct / 100.0)

    partial_fill_rate = sum(1 for r in rows if str(r.fill_status) == "PARTIAL") / total
    avg_snapshot_age_ms = sum(float(r.snapshot_age_ms or 0.0) for r in rows) / total
    avg_execution_latency_ms = sum(float(r.execution_latency_ms or 0.0) for r in rows) / total
    avg_snapshot_to_decision_ms = sum(float(r.snapshot_to_decision_ms or 0.0) for r in rows) / total
    avg_decision_to_submission_ms = sum(float(r.decision_to_submission_ms or 0.0) for r in rows) / total
    avg_submission_to_inclusion_ms = sum(float(r.submission_to_inclusion_ms or 0.0) for r in rows) / total
    slippage_samples = [float(r.slippage_vs_top) for r in rows if r.slippage_vs_top is not None]
    avg_slippage_vs_top = 0.0 if not slippage_samples else (sum(slippage_samples) / len(slippage_samples))

    failures: dict[str, int] = {}
    for row in rows:
        reason = row.failure_reason or ("UNFILLED" if str(row.fill_status) == "UNFILLED" else None)
        if reason is None:
            continue
        failures[reason] = failures.get(reason, 0) + 1

    failure_rate_by_reason = {k: v / total for k, v in sorted(failures.items(), key=lambda it: it[0])}

    return {
        "sample_size": total,
        "fill_efficiency": round(fill_efficiency, 6),
        "avg_levels_consumed": round(avg_levels_consumed, 6),
        "levels_consumed_avg": round(avg_levels_consumed, 6),
        "queue_impact_pct": round(queue_impact_pct, 6),
        "effective_vs_raw_liquidity": round(effective_vs_raw_liquidity, 6),
        "partial_fill_rate": round(partial_fill_rate, 6),
        "avg_snapshot_age_ms": round(avg_snapshot_age_ms, 6),
        "avg_execution_latency_ms": round(avg_execution_latency_ms, 6),
        "avg_snapshot_to_decision_ms": round(avg_snapshot_to_decision_ms, 6),
        "avg_decision_to_submission_ms": round(avg_decision_to_submission_ms, 6),
        "avg_submission_to_inclusion_ms": round(avg_submission_to_inclusion_ms, 6),
        "avg_slippage_vs_top": round(avg_slippage_vs_top, 6),
        "failure_rate_by_reason": failure_rate_by_reason,
    }


@router.get("/execution/{execution_id}")
def get_execution(execution_id: int, request: Request) -> dict[str, object]:
    container = request.app.state.container
    with container.session_factory() as session:
        row = session.get(ExecutionRecord, execution_id)
    if row is None:
        raise HTTPException(status_code=404, detail="execution not found")
    return row.model_dump()
