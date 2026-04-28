from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.models import ExecutionRecord, XRPLOrderbookSnapshot


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


@dataclass(slots=True)
class ShadowExecutionRequest:
    token_id: int
    signal_id: int
    side: str
    requested_size_xrp: float
    entry_ledger: int
    snapshots: list[XRPLOrderbookSnapshot]
    max_hold_ledgers: int = 3


class ShadowExecutionLoop:
    """Ledger-close-only execution reconstruction for XRPL shadow mode."""

    def simulate(self, data: ShadowExecutionRequest) -> ExecutionRecord:
        ordered = sorted(data.snapshots, key=lambda snap: int(snap.ledger_index))
        entry_candidates = [snap for snap in ordered if int(snap.ledger_index) == int(data.entry_ledger)]
        if not entry_candidates:
            raise ValueError("ENTRY_LEDGER_NOT_FOUND")

        entry_snapshot = entry_candidates[0]
        eligible_ledgers = [
            snap
            for snap in ordered
            if int(snap.ledger_index) >= int(data.entry_ledger) + 1
            and int(snap.ledger_index) <= int(data.entry_ledger) + max(1, int(data.max_hold_ledgers))
        ]

        chosen_snapshot: XRPLOrderbookSnapshot | None = None
        filled_size = 0.0
        avg_fill_price: float | None = None
        fill_status = "UNFILLED"
        failure_reason = "NO_ELIGIBLE_LEDGER_CLOSE"

        for snapshot in eligible_ledgers:
            visible_depth = max(0.0, float(snapshot.ask_depth_xrp)) if str(data.side).upper() == "BUY" else max(0.0, float(snapshot.bid_depth_xrp))
            if visible_depth <= 0:
                continue

            executable_depth = visible_depth * 0.65
            filled_size = min(max(0.0, float(data.requested_size_xrp)), executable_depth)
            if filled_size <= 0:
                continue

            chosen_snapshot = snapshot
            avg_fill_price = float(snapshot.best_ask if str(data.side).upper() == "BUY" else snapshot.best_bid)
            fill_status = "FILLED" if filled_size + 1e-9 >= float(data.requested_size_xrp) else "PARTIAL"
            failure_reason = None
            break

        execution_snapshot = chosen_snapshot or eligible_ledgers[-1] if eligible_ledgers else entry_snapshot
        execution_time = _utc(execution_snapshot.observed_at)
        snapshot_time = _utc(entry_snapshot.observed_at)
        signal_time = snapshot_time
        snapshot_age_ms = max(0, int((execution_time - snapshot_time).total_seconds() * 1000.0))
        inclusion_delay_ledgers = max(0, int(execution_snapshot.ledger_index) - int(entry_snapshot.ledger_index))
        fill_levels_json = []
        if chosen_snapshot is not None and filled_size > 0 and avg_fill_price is not None:
            fill_levels_json = [{"ledger_index": int(chosen_snapshot.ledger_index), "filled_size": round(filled_size, 6), "price": round(avg_fill_price, 6)}]

        return ExecutionRecord(
            token_id=int(data.token_id),
            signal_id=int(data.signal_id),
            risk_decision_id=None,
            snapshot_id=0,
            position_id=None,
            side=str(data.side).upper(),
            requested_size=float(data.requested_size_xrp),
            filled_size=round(filled_size, 6),
            fill_status=fill_status,
            avg_fill_price=avg_fill_price,
            fill_levels_json=fill_levels_json,
            slippage_vs_top=(None if avg_fill_price is None or float(entry_snapshot.best_ask or 0.0) <= 0 else max(0.0, ((float(avg_fill_price) - float(entry_snapshot.best_ask)) / float(entry_snapshot.best_ask)) * 100.0)),
            snapshot_time=snapshot_time,
            signal_time=signal_time,
            execution_time=execution_time,
            ledger_index_snapshot=int(entry_snapshot.ledger_index),
            ledger_index_signal=int(entry_snapshot.ledger_index),
            ledger_index_execution=int(execution_snapshot.ledger_index),
            ledger_index_inclusion=int(execution_snapshot.ledger_index),
            snapshot_to_decision_ms=0,
            decision_to_submission_ms=0,
            submission_to_inclusion_ms=max(0, snapshot_age_ms),
            total_execution_latency_ms=max(0, snapshot_age_ms),
            inclusion_delay_ledgers=inclusion_delay_ledgers,
            inclusion_status="SHADOW" if chosen_snapshot is not None else "NO_FILL",
            inclusion_failure_reason=failure_reason,
            execution_latency_ms=max(0, snapshot_age_ms),
            snapshot_age_ms=max(0, snapshot_age_ms),
            holding_time_ms=max(0, snapshot_age_ms),
            failure_reason=failure_reason,
            execution_details_json=json.dumps(
                {
                    "shadow": True,
                    "execution_mode": "ledger_aligned",
                    "mid_ledger_fills_disabled": True,
                    "entry_ledger": int(data.entry_ledger),
                    "evaluated_ledgers": [int(snap.ledger_index) for snap in eligible_ledgers],
                }
            ),
        )