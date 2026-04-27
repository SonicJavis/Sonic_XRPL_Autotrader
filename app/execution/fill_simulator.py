from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


def _utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


@dataclass(slots=True)
class ExecutionResult:
    requested_size: float
    filled_size: float
    avg_entry_price: float | None
    avg_exit_price: float | None
    fill_status: str
    slippage_pct: float | None
    execution_latency_ms: int
    failure_reason: str | None
    snapshot_age_ms: int
    fill_levels: list[dict[str, float | int]]

    @property
    def fill_success(self) -> bool:
        return self.fill_status == "FULL"

    @property
    def partial_fill(self) -> bool:
        return self.fill_status == "PARTIAL"

    def to_legacy_dict(self) -> dict[str, float | bool]:
        slippage = float(self.slippage_pct or 0.0)
        if self.fill_status == "UNFILLED" and slippage == 0.0:
            slippage = 100.0
        return {
            "filled_size_xrp": self.filled_size,
            "avg_price": float(self.avg_entry_price or 0.0),
            "slippage_pct": slippage,
            "fill_success": self.fill_success,
            "partial_fill": self.partial_fill,
        }


def validate_orderbook(parsed: dict[str, object]) -> tuple[bool, str | None]:
    bids = list(parsed.get("bids", []))
    asks = list(parsed.get("asks", []))
    if not bids or not asks:
        return False, "INVALID_ORDERBOOK"

    best_bid = float(bids[0].get("price", 0.0))
    best_ask = float(asks[0].get("price", 0.0))
    if best_bid <= 0 or best_ask <= 0 or best_bid >= best_ask:
        return False, "INVALID_ORDERBOOK"
    return True, None


def _fill_status(requested: float, filled: float) -> str:
    if filled <= 1e-12:
        return "UNFILLED"
    if filled + 1e-9 >= requested:
        return "FULL"
    return "PARTIAL"


def _snapshot_age_ms(snapshot_time: datetime, signal_time: datetime, execution_latency_ms: int) -> tuple[int, datetime]:
    snap = _utc(snapshot_time)
    sig = _utc(signal_time)
    execution_time = sig + timedelta(milliseconds=max(0, execution_latency_ms))
    age_ms = int((execution_time - snap).total_seconds() * 1000.0)
    return max(0, age_ms), execution_time


def simulate_entry_buy(
    *,
    asks: list[dict[str, float]],
    best_bid: float,
    best_ask: float,
    requested_size_xrp: float,
    snapshot_time: datetime,
    signal_time: datetime,
    execution_latency_ms: int,
    max_snapshot_age_ms: int,
    liquidity_haircut_pct: float,
) -> ExecutionResult:
    requested = max(0.0, float(requested_size_xrp))
    age_ms, _ = _snapshot_age_ms(snapshot_time, signal_time, execution_latency_ms)
    if age_ms > max_snapshot_age_ms:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=execution_latency_ms,
            failure_reason="STALE_MARKET_DATA",
            snapshot_age_ms=age_ms,
            fill_levels=[],
        )

    if requested <= 0:
        return ExecutionResult(
            requested_size=0.0,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=execution_latency_ms,
            failure_reason="NO_REQUESTED_SIZE",
            snapshot_age_ms=age_ms,
            fill_levels=[],
        )

    if not asks or best_bid <= 0 or best_ask <= 0 or best_bid >= best_ask:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=execution_latency_ms,
            failure_reason="INVALID_ORDERBOOK",
            snapshot_age_ms=age_ms,
            fill_levels=[],
        )

    haircut = max(0.0, min(0.95, liquidity_haircut_pct))
    remaining_xrp = requested
    spent_xrp = 0.0
    tokens_bought = 0.0
    levels_used: list[dict[str, float | int]] = []

    for idx, level in enumerate(asks):
        price = float(level.get("price", 0.0))
        xrp_value = float(level.get("xrp_value", 0.0)) * (1.0 - haircut)
        token_amount = float(level.get("token_amount", 0.0)) * (1.0 - haircut)
        if price <= 0 or xrp_value <= 0 or token_amount <= 0:
            continue

        take_xrp = min(remaining_xrp, xrp_value)
        token_take = (take_xrp / xrp_value) * token_amount
        spent_xrp += take_xrp
        tokens_bought += token_take
        levels_used.append(
            {
                "level_index": idx,
                "side": "ask",
                "price": price,
                "consumed_xrp": take_xrp,
                "consumed_tokens": token_take,
            }
        )
        remaining_xrp -= take_xrp
        if remaining_xrp <= 0:
            break

    if spent_xrp <= 0 or tokens_bought <= 0:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=execution_latency_ms,
            failure_reason="NO_LIQUIDITY",
            snapshot_age_ms=age_ms,
            fill_levels=[],
        )

    avg_entry = spent_xrp / tokens_bought
    slippage: float | None = None
    if best_ask > 0:
        slippage = max(0.0, ((avg_entry - best_ask) / best_ask) * 100.0)
    status = _fill_status(requested, spent_xrp)
    reason = None
    if status == "UNFILLED":
        reason = "NO_LIQUIDITY"
    elif status == "PARTIAL":
        reason = "PARTIAL_FILL"

    return ExecutionResult(
        requested_size=requested,
        filled_size=spent_xrp,
        avg_entry_price=avg_entry,
        avg_exit_price=None,
        fill_status=status,
        slippage_pct=slippage,
        execution_latency_ms=execution_latency_ms,
        failure_reason=reason,
        snapshot_age_ms=age_ms,
        fill_levels=levels_used,
    )


def simulate_exit_sell(
    *,
    bids: list[dict[str, float]],
    best_bid: float,
    best_ask: float,
    requested_token_size: float,
    snapshot_time: datetime,
    signal_time: datetime,
    execution_latency_ms: int,
    max_snapshot_age_ms: int,
    liquidity_haircut_pct: float,
) -> ExecutionResult:
    requested = max(0.0, float(requested_token_size))
    age_ms, _ = _snapshot_age_ms(snapshot_time, signal_time, execution_latency_ms)
    if age_ms > max_snapshot_age_ms:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=execution_latency_ms,
            failure_reason="STALE_MARKET_DATA",
            snapshot_age_ms=age_ms,
            fill_levels=[],
        )

    if requested <= 0:
        return ExecutionResult(
            requested_size=0.0,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=execution_latency_ms,
            failure_reason="NO_REQUESTED_SIZE",
            snapshot_age_ms=age_ms,
            fill_levels=[],
        )

    if not bids or best_bid <= 0 or best_ask <= 0 or best_bid >= best_ask:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=execution_latency_ms,
            failure_reason="NO_BIDS",
            snapshot_age_ms=age_ms,
            fill_levels=[],
        )

    haircut = max(0.0, min(0.95, liquidity_haircut_pct))
    remaining_tokens = requested
    sold_tokens = 0.0
    proceeds_xrp = 0.0
    levels_used: list[dict[str, float | int]] = []

    for idx, level in enumerate(bids):
        price = float(level.get("price", 0.0))
        token_amount = float(level.get("token_amount", 0.0)) * (1.0 - haircut)
        if price <= 0 or token_amount <= 0:
            continue

        take_tokens = min(remaining_tokens, token_amount)
        proceeds_xrp += take_tokens * price
        sold_tokens += take_tokens
        levels_used.append(
            {
                "level_index": idx,
                "side": "bid",
                "price": price,
                "consumed_tokens": take_tokens,
                "proceeds_xrp": take_tokens * price,
            }
        )
        remaining_tokens -= take_tokens
        if remaining_tokens <= 0:
            break

    if sold_tokens <= 0:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=execution_latency_ms,
            failure_reason="NO_BIDS",
            snapshot_age_ms=age_ms,
            fill_levels=[],
        )

    avg_exit = proceeds_xrp / sold_tokens
    slippage: float | None = None
    if best_bid > 0:
        slippage = max(0.0, ((best_bid - avg_exit) / best_bid) * 100.0)
    status = _fill_status(requested, sold_tokens)
    reason = "PARTIAL_EXIT" if status == "PARTIAL" else None

    return ExecutionResult(
        requested_size=requested,
        filled_size=sold_tokens,
        avg_entry_price=None,
        avg_exit_price=avg_exit,
        fill_status=status,
        slippage_pct=slippage,
        execution_latency_ms=execution_latency_ms,
        failure_reason=reason,
        snapshot_age_ms=age_ms,
        fill_levels=levels_used,
    )


def simulate_fill(asks: list[dict[str, float]], target_size_xrp: float) -> dict[str, float | bool]:
    """Compatibility wrapper used by older call-sites/tests."""
    best_ask = float(asks[0].get("price", 0.0)) if asks else 0.0
    best_bid = best_ask * 0.999 if best_ask > 0 else 0.0
    now = datetime.now(tz=timezone.utc)
    out = simulate_entry_buy(
        asks=asks,
        best_bid=best_bid,
        best_ask=best_ask,
        requested_size_xrp=target_size_xrp,
        snapshot_time=now,
        signal_time=now,
        execution_latency_ms=0,
        max_snapshot_age_ms=1_000_000,
        liquidity_haircut_pct=0.0,
    )
    return out.to_legacy_dict()
