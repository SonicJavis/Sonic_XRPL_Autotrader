from __future__ import annotations

import hashlib
import json

from sqlmodel import Session, select

from app.db.models import ExecutionFillSlice, ExecutionRecord, Position, PositionExitFill


class ReplayEngine:
    @staticmethod
    def _checksum_slices(slices: list[ExecutionFillSlice]) -> str:
        payload = [
            {
                "id": int(s.id or 0),
                "execution_id": int(s.execution_id),
                "ledger_index": int(s.ledger_index),
                "fill_status": str(s.fill_status),
                "filled_size": float(s.filled_size),
                "avg_price": (None if s.avg_price is None else float(s.avg_price)),
                "fill_levels_json": list(s.fill_levels_json or []),
            }
            for s in slices
        ]
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def _derive_fill_status(requested: float, filled: float) -> str:
        if filled <= 1e-12:
            return "UNFILLED"
        if filled + 1e-9 >= requested:
            return "FILLED"
        return "PARTIAL"

    def replay_execution(self, session: Session, execution_id: int) -> dict[str, object]:
        row = session.get(ExecutionRecord, execution_id)
        if row is None:
            return {"status": "NOT_FOUND", "execution_id": execution_id}

        slices = session.exec(
            select(ExecutionFillSlice)
            .where(ExecutionFillSlice.execution_id == execution_id)
            .order_by(ExecutionFillSlice.id.asc())
        ).all()

        replay_filled_size = float(sum(float(s.filled_size or 0.0) for s in slices))
        weighted_notional = sum(float(s.filled_size or 0.0) * float(s.avg_price or 0.0) for s in slices if s.avg_price is not None)
        replay_vwap = (weighted_notional / replay_filled_size) if replay_filled_size > 0 else None
        replay_fill_status = self._derive_fill_status(float(row.requested_size), replay_filled_size)

        realized_rows = session.exec(
            select(PositionExitFill)
            .where(PositionExitFill.execution_id == execution_id)
            .order_by(PositionExitFill.id.asc())
        ).all()
        replay_realized_pnl = float(sum(float(r.pnl_xrp or 0.0) for r in realized_rows))

        details = json.loads(row.execution_details_json or "{}")
        expected_checksum = str(details.get("slice_levels_checksum", ""))
        replay_checksum = self._checksum_slices(slices)

        mismatches: list[str] = []
        if abs(replay_filled_size - float(row.filled_size or 0.0)) > 1e-9:
            mismatches.append("filled_size_mismatch")
        if replay_vwap is not None and row.avg_fill_price is not None and abs(float(replay_vwap) - float(row.avg_fill_price)) > 1e-9:
            mismatches.append("vwap_mismatch")
        if replay_fill_status != str(row.fill_status):
            mismatches.append("fill_status_mismatch")
        if expected_checksum and replay_checksum != expected_checksum:
            mismatches.append("slice_levels_checksum_mismatch")

        linked_position = session.get(Position, row.position_id) if row.position_id else None

        status = "REPLAY_OK" if not mismatches else "REPLAY_MISMATCH"
        return {
            "status": status,
            "execution_id": execution_id,
            "requested_size": float(row.requested_size),
            "filled_size": replay_filled_size,
            "avg_fill_price": replay_vwap,
            "slippage_vs_top": (None if row.slippage_vs_top is None else float(row.slippage_vs_top)),
            "fill_status": replay_fill_status,
            "failure_reason": row.failure_reason,
            "realized_pnl_xrp": replay_realized_pnl,
            "position_id": row.position_id,
            "position_status": (linked_position.status if linked_position is not None else None),
            "slice_count": len(slices),
            "mismatches": mismatches,
        }
