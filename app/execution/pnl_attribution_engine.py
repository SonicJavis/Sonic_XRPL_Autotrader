from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json

from sqlmodel import Session, select

from app.db.models import (
    AlphaSignal,
    ExecutionRecord,
    MarketDepthLevel,
    MarketSnapshot,
    Position,
    PositionExitFill,
)
from app.execution.fill_simulator import ExecutionResult, simulate_exit_sell


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


@dataclass(slots=True)
class ExitDecision:
    should_exit: bool
    reason: str
    urgency: str
    approved_by_risk: bool


class PnLAttributionEngine:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _token_key(currency: str, issuer: str) -> str:
        return f"{currency}:{issuer}"

    @staticmethod
    def _position_status(remaining_size: float) -> str:
        if remaining_size <= 1e-9:
            return "CLOSED"
        return "PARTIAL_EXIT"

    @staticmethod
    def _is_transient_exit_failure(reason: str | None) -> bool:
        return reason in {"NO_BIDS", "NO_LIQUIDITY", "STALE_MARKET_DATA"}

    @staticmethod
    def _ledger_index_for_time(ts: datetime, ledger_close_ms: int) -> int:
        unix_ms = int(_utc(ts).timestamp() * 1000.0)
        return max(0, unix_ms // max(1, int(ledger_close_ms)))

    @staticmethod
    def evaluate_exit_decision(
        *,
        position: Position,
        snapshot: MarketSnapshot,
        now: datetime,
        min_exit_retry_ms: int,
        max_exit_retries: int,
        approved_by_risk: bool,
    ) -> ExitDecision:
        if position.status in {"EXIT_FAILED_PERMANENT", "CLOSED"}:
            return ExitDecision(False, "terminal_position_state", "LOW", approved_by_risk)

        if position.exit_attempt_count >= max_exit_retries and position.status != "PARTIAL_EXIT":
            return ExitDecision(False, "max_exit_retries_reached", "LOW", approved_by_risk)

        if position.status == "OPEN":
            return ExitDecision(False, "no_exit_signal", "LOW", approved_by_risk)

        if position.status == "EXIT_FAILED_TRANSIENT" and position.last_exit_attempt_time is not None:
            elapsed = (_utc(now) - _utc(position.last_exit_attempt_time)).total_seconds() * 1000.0
            if elapsed < float(min_exit_retry_ms):
                return ExitDecision(False, "retry_cooldown_active", "LOW", approved_by_risk)

        if not approved_by_risk:
            return ExitDecision(False, "risk_not_approved", "MEDIUM", approved_by_risk)

        return ExitDecision(True, "exit_requested", "HIGH" if position.status == "PARTIAL_EXIT" else "MEDIUM", approved_by_risk)

    def create_execution_record(
        self,
        session: Session,
        *,
        token_id: int,
        signal_id: int,
        risk_decision_id: int | None,
        snapshot_id: int,
        position_id: str | None,
        side: str,
        execution_result: ExecutionResult,
        snapshot_time: datetime,
        signal_time: datetime,
        execution_time: datetime,
        ledger_index_snapshot: int | None = None,
        ledger_index_signal: int | None = None,
        ledger_index_execution: int | None = None,
        ledger_index_inclusion: int | None = None,
        xrpl_ledger_close_ms: int = 4000,
        min_ledger_delay: int = 1,
        max_ledger_delay: int = 3,
        holding_time_ms: int = 0,
    ) -> ExecutionRecord:
        s_time = _utc(snapshot_time)
        sig_time = _utc(signal_time)
        ex_time = _utc(execution_time)
        if ex_time < sig_time or sig_time < s_time:
            raise ValueError("FAILED_INVALID_TIMING")

        s_ledger = (
            int(ledger_index_snapshot)
            if ledger_index_snapshot is not None
            else self._ledger_index_for_time(s_time, xrpl_ledger_close_ms)
        )
        sig_ledger = (
            int(ledger_index_signal)
            if ledger_index_signal is not None
            else self._ledger_index_for_time(sig_time, xrpl_ledger_close_ms)
        )
        ex_ledger_default = max(sig_ledger, sig_ledger + max(0, int(min_ledger_delay)) - 1)
        ex_ledger = int(ledger_index_execution) if ledger_index_execution is not None else ex_ledger_default
        incl_ledger = (
            int(ledger_index_inclusion)
            if ledger_index_inclusion is not None
            else ex_ledger + max(0, int(min_ledger_delay))
        )

        if sig_ledger < s_ledger or ex_ledger < sig_ledger or incl_ledger < ex_ledger:
            raise ValueError("FAILED_INVALID_LEDGER_TIMING")
        ledger_delay = incl_ledger - ex_ledger
        if ledger_delay < max(0, int(min_ledger_delay)) or ledger_delay > max(0, int(max_ledger_delay)):
            raise ValueError("FAILED_INVALID_LEDGER_TIMING")

        record = ExecutionRecord(
            token_id=token_id,
            signal_id=signal_id,
            risk_decision_id=risk_decision_id,
            snapshot_id=snapshot_id,
            position_id=position_id,
            side=side,
            requested_size=execution_result.requested_size,
            filled_size=execution_result.filled_size,
            fill_status=execution_result.fill_status,
            avg_fill_price=execution_result.avg_entry_price if side.upper() == "BUY" else execution_result.avg_exit_price,
            fill_levels_json=execution_result.fill_levels,
            slippage_vs_top=execution_result.slippage_pct,
            snapshot_time=s_time,
            signal_time=sig_time,
            execution_time=ex_time,
            ledger_index_snapshot=s_ledger,
            ledger_index_signal=sig_ledger,
            ledger_index_execution=ex_ledger,
            ledger_index_inclusion=incl_ledger,
            execution_latency_ms=execution_result.execution_latency_ms,
            snapshot_age_ms=execution_result.snapshot_age_ms,
            holding_time_ms=holding_time_ms,
            failure_reason=execution_result.failure_reason,
            execution_details_json=json.dumps(
                {
                    "fill_success": execution_result.fill_success,
                    "partial_fill": execution_result.partial_fill,
                }
            ),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record

    def create_position_from_entry(
        self,
        session: Session,
        *,
        token_id: int,
        issuer: str,
        currency: str,
        signal_id: int,
        risk_decision_id: int | None,
        execution_record_id: int,
        snapshot_id: int,
        execution_result: ExecutionResult,
        alpha_signal: AlphaSignal | None,
        execution_time: datetime,
    ) -> Position | None:
        if execution_result.filled_size <= 0 or execution_result.avg_entry_price is None:
            return None

        position = Position(
            issuer=issuer,
            currency=currency,
            token_id=token_id,
            signal_id=signal_id,
            risk_decision_id=risk_decision_id,
            execution_id=execution_record_id,
            entry_time=_utc(execution_time),
            entry_vwap=execution_result.avg_entry_price,
            entry_filled_size=execution_result.filled_size,
            remaining_size=execution_result.filled_size,
            entry_orderbook_snapshot_id=snapshot_id,
            status="OPEN",
            component_scores_json=(alpha_signal.component_scores_json if alpha_signal is not None else "{}"),
            risk_flags_json=(alpha_signal.manipulation_flags_json if alpha_signal is not None else "{}"),
            execution_details_json=json.dumps(
                {
                    "entry_fill_status": execution_result.fill_status,
                    "entry_levels": execution_result.fill_levels,
                    "entry_slippage_vs_top": execution_result.slippage_pct,
                    "entry_latency_ms": execution_result.execution_latency_ms,
                    "entry_snapshot_age_ms": execution_result.snapshot_age_ms,
                }
            ),
        )
        session.add(position)
        session.commit()
        session.refresh(position)

        exec_row = session.get(ExecutionRecord, execution_record_id)
        if exec_row is not None:
            exec_row.position_id = position.position_id
            session.add(exec_row)
            session.commit()

        return position

    def _depth_for_snapshot(self, session: Session, snapshot_id: int) -> tuple[list[dict[str, float]], list[dict[str, float]], float, float]:
        levels = session.exec(
            select(MarketDepthLevel)
            .where(MarketDepthLevel.snapshot_id == snapshot_id)
            .order_by(MarketDepthLevel.side.asc(), MarketDepthLevel.level_index.asc())
        ).all()
        bids = [
            {"price": row.price_xrp_per_token, "token_amount": row.token_amount, "xrp_value": row.xrp_value}
            for row in levels
            if row.side == "bid"
        ]
        asks = [
            {"price": row.price_xrp_per_token, "token_amount": row.token_amount, "xrp_value": row.xrp_value}
            for row in levels
            if row.side == "ask"
        ]
        best_bid = float(bids[0]["price"]) if bids else 0.0
        best_ask = float(asks[0]["price"]) if asks else 0.0
        return bids, asks, best_bid, best_ask

    def simulate_unrealized_for_position(
        self,
        session: Session,
        *,
        position: Position,
        snapshot: MarketSnapshot,
        execution_latency_ms: int,
        max_snapshot_age_ms: int,
        liquidity_haircut_pct: float,
        latency_haircut_pct: float = 0.0,
        contention_haircut_pct: float = 0.0,
        trustline_liquidity_discount_pct: float = 0.0,
        ledger_drift_pct: float = 0.0,
        min_level_xrp: float = 0.0,
        max_levels: int | None = None,
    ) -> dict[str, object]:
        if snapshot.id is None:
            return {"unrealized_pnl": None, "unrealized_exit_vwap": None, "unrealized_fillable_size": 0.0, "reason": "INVALID_ORDERBOOK"}

        bids, asks, best_bid, best_ask = self._depth_for_snapshot(session, snapshot.id)
        requested_tokens = position.remaining_size / position.entry_vwap if position.entry_vwap > 0 else 0.0

        result = simulate_exit_sell(
            bids=bids,
            best_bid=best_bid,
            best_ask=best_ask,
            requested_token_size=requested_tokens,
            snapshot_time=snapshot.created_at,
            signal_time=datetime.now(tz=timezone.utc),
            execution_latency_ms=execution_latency_ms,
            max_snapshot_age_ms=max_snapshot_age_ms,
            liquidity_haircut_pct=liquidity_haircut_pct,
            latency_haircut_pct=latency_haircut_pct,
            contention_haircut_pct=contention_haircut_pct,
            trustline_liquidity_discount_pct=trustline_liquidity_discount_pct,
            ledger_drift_pct=ledger_drift_pct,
            min_level_xrp=min_level_xrp,
            max_levels=max_levels,
        )

        if result.avg_exit_price is None or result.filled_size <= 0:
            return {
                "unrealized_pnl": None,
                "unrealized_exit_vwap": None,
                "unrealized_fillable_size": 0.0,
                "reason": result.failure_reason,
            }

        sold_xrp = result.avg_exit_price * result.filled_size
        unrealized_pnl = sold_xrp - (position.entry_vwap * result.filled_size)
        return {
            "unrealized_pnl": unrealized_pnl,
            "unrealized_exit_vwap": result.avg_exit_price,
            "unrealized_fillable_size": result.filled_size,
            "reason": result.failure_reason,
        }

    def update_positions_for_snapshot(
        self,
        session: Session,
        *,
        token_id: int,
        snapshot: MarketSnapshot,
        execution_latency_ms: int,
        max_snapshot_age_ms: int,
        liquidity_haircut_pct: float,
        latency_haircut_pct: float = 0.0,
        contention_haircut_pct: float = 0.0,
        trustline_liquidity_discount_pct: float = 0.0,
        ledger_drift_pct: float = 0.0,
        min_level_xrp: float = 0.0,
        max_levels: int | None = None,
        min_exit_retry_ms: int,
        max_exit_retries: int,
        approve_exit_fn=None,
    ) -> None:
        if snapshot.id is None:
            return

        open_positions = session.exec(
            select(Position)
            .where(Position.token_id == token_id)
            .where(Position.status.in_(["OPEN", "EXIT_PENDING", "PARTIAL_EXIT", "EXIT_FAILED_TRANSIENT"]))
            .order_by(Position.entry_time.asc())
        ).all()

        for position in open_positions:
            approved_by_risk = True if approve_exit_fn is None else bool(approve_exit_fn(position, snapshot))
            decision = self.evaluate_exit_decision(
                position=position,
                snapshot=snapshot,
                now=datetime.now(tz=timezone.utc),
                min_exit_retry_ms=min_exit_retry_ms,
                max_exit_retries=max_exit_retries,
                approved_by_risk=approved_by_risk,
            )
            if not decision.should_exit:
                continue

            bids, asks, best_bid, best_ask = self._depth_for_snapshot(session, snapshot.id)
            requested_tokens = position.remaining_size / position.entry_vwap if position.entry_vwap > 0 else 0.0
            exec_result = simulate_exit_sell(
                bids=bids,
                best_bid=best_bid,
                best_ask=best_ask,
                requested_token_size=requested_tokens,
                snapshot_time=snapshot.created_at,
                signal_time=datetime.now(tz=timezone.utc),
                execution_latency_ms=execution_latency_ms,
                max_snapshot_age_ms=max_snapshot_age_ms,
                liquidity_haircut_pct=liquidity_haircut_pct,
                latency_haircut_pct=latency_haircut_pct,
                contention_haircut_pct=contention_haircut_pct,
                trustline_liquidity_discount_pct=trustline_liquidity_discount_pct,
                ledger_drift_pct=ledger_drift_pct,
                min_level_xrp=min_level_xrp,
                max_levels=max_levels,
            )

            holding_ms = int((datetime.now(tz=timezone.utc) - _utc(position.entry_time)).total_seconds() * 1000.0)
            exec_row = self.create_execution_record(
                session,
                token_id=position.token_id,
                signal_id=position.signal_id,
                risk_decision_id=position.risk_decision_id,
                snapshot_id=snapshot.id,
                position_id=position.position_id,
                side="SELL",
                execution_result=exec_result,
                snapshot_time=snapshot.created_at,
                signal_time=datetime.now(tz=timezone.utc),
                execution_time=datetime.now(tz=timezone.utc),
                holding_time_ms=max(0, holding_ms),
            )

            position.exit_attempt_count += 1
            position.last_exit_attempt_time = datetime.now(tz=timezone.utc)

            if exec_result.filled_size <= 0 or exec_result.avg_exit_price is None:
                failure = exec_result.failure_reason or "EXIT_FAILED"
                if self._is_transient_exit_failure(failure):
                    position.status = "EXIT_FAILED_TRANSIENT"
                else:
                    position.status = "EXIT_FAILED_PERMANENT"
                position.failure_reason = failure
                position.exit_failure_reason = failure
                position.exit_orderbook_snapshot_id = snapshot.id
                session.add(position)
                session.commit()
                continue

            proposed_exit_filled = position.exit_filled_size + exec_result.filled_size
            if proposed_exit_filled > (position.entry_filled_size + 1e-9):
                raise ValueError("CRITICAL_OVERFILL_DETECTED")

            fill_xrp = exec_result.avg_exit_price * exec_result.filled_size
            cost_xrp = position.entry_vwap * exec_result.filled_size
            pnl = fill_xrp - cost_xrp

            session.add(
                PositionExitFill(
                    position_id=position.position_id,
                    execution_id=exec_row.id,
                    snapshot_id=snapshot.id,
                    exit_time=datetime.now(tz=timezone.utc),
                    exit_vwap=exec_result.avg_exit_price,
                    fill_size=exec_result.filled_size,
                    pnl_xrp=pnl,
                    fill_levels_json=exec_result.fill_levels,
                    failure_reason=exec_result.failure_reason,
                )
            )

            prior_remaining = position.remaining_size
            position.exit_filled_size = proposed_exit_filled
            position.remaining_size = max(0.0, position.entry_filled_size - position.exit_filled_size)
            if position.remaining_size > (prior_remaining + 1e-9):
                raise ValueError("CRITICAL_SIZE_DRIFT_DETECTED")
            position.exit_vwap = exec_result.avg_exit_price
            position.exit_orderbook_snapshot_id = snapshot.id
            position.status = self._position_status(position.remaining_size)
            position.exit_failure_reason = None
            if position.remaining_size <= 1e-9:
                position.exit_time = datetime.now(tz=timezone.utc)
            session.add(position)
            session.commit()

    def realized_pnl_summary(self, session: Session) -> dict[str, object]:
        fills = session.exec(select(PositionExitFill).order_by(PositionExitFill.id.asc())).all()
        realized = sum(float(row.pnl_xrp) for row in fills)
        return {
            "realized_pnl_xrp": realized,
            "exit_fill_count": len(fills),
            "records": [row.model_dump() for row in fills],
        }

    def unrealized_pnl_summary(
        self,
        session: Session,
        *,
        execution_latency_ms: int,
        max_snapshot_age_ms: int,
        liquidity_haircut_pct: float,
        latency_haircut_pct: float = 0.0,
        contention_haircut_pct: float = 0.0,
        trustline_liquidity_discount_pct: float = 0.0,
        ledger_drift_pct: float = 0.0,
    ) -> dict[str, object]:
        rows: list[dict[str, object]] = []
        total = 0.0
        any_null = False

        open_positions = session.exec(
            select(Position)
            .where(Position.status.in_(["OPEN", "EXIT_PENDING", "PARTIAL_EXIT", "EXIT_FAILED_TRANSIENT", "EXIT_FAILED_PERMANENT"]))
            .order_by(Position.entry_time.asc())
        ).all()
        for position in open_positions:
            latest = session.exec(
                select(MarketSnapshot)
                .where(MarketSnapshot.token_id == position.token_id)
                .order_by(MarketSnapshot.created_at.desc())
            ).first()
            if latest is None:
                any_null = True
                rows.append({"position_id": position.position_id, "unrealized_pnl": None, "reason": "NO_SNAPSHOT"})
                continue

            u = self.simulate_unrealized_for_position(
                session,
                position=position,
                snapshot=latest,
                execution_latency_ms=execution_latency_ms,
                max_snapshot_age_ms=max_snapshot_age_ms,
                liquidity_haircut_pct=liquidity_haircut_pct,
                latency_haircut_pct=latency_haircut_pct,
                contention_haircut_pct=contention_haircut_pct,
                trustline_liquidity_discount_pct=trustline_liquidity_discount_pct,
                ledger_drift_pct=ledger_drift_pct,
            )
            rows.append({"position_id": position.position_id, **u})
            if u["unrealized_pnl"] is None:
                any_null = True
            else:
                total += float(u["unrealized_pnl"])

        return {
            "unrealized_pnl_xrp": (None if any_null else total),
            "positions": rows,
        }

    def list_failures(self, session: Session, limit: int = 200) -> list[dict[str, object]]:
        rows = session.exec(
            select(ExecutionRecord)
            .where(ExecutionRecord.failure_reason != None)
            .order_by(ExecutionRecord.id.desc())
            .limit(limit)
        ).all()
        return [row.model_dump() for row in rows]
