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
    snapshot_to_decision_ms: int
    decision_to_submission_ms: int
    submission_to_inclusion_ms: int
    total_execution_latency_ms: int
    execution_window_snapshots: int
    drifted_best_bid: float | None
    drifted_best_ask: float | None
    failure_reason: str | None
    snapshot_age_ms: int
    queue_haircut_pct: float
    latency_haircut_pct: float
    contention_haircut_pct: float
    trustline_liquidity_discount_pct: float
    ledger_drift_pct: float
    effective_liquidity_ratio: float
    fill_levels: list[dict[str, float | int]]
    consumed_levels_detailed: list[dict[str, float | int]]

    @property
    def fill_success(self) -> bool:
        return self.fill_status in {"FILLED", "FULL"}

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
        return "FILLED"
    return "PARTIAL"


def _clamp_pct(raw: float) -> float:
    return max(0.0, min(0.95, float(raw)))


def _degradation_multiplier(*, queue: float, latency: float, contention: float, trustline: float, fundedness: float, drift: float) -> float:
    # Apply independent execution degradations multiplicatively to avoid optimistic overfills.
    mul = 1.0
    for pct in (queue, latency, contention, trustline, fundedness, drift):
        mul *= 1.0 - _clamp_pct(pct)
    return max(0.0, min(1.0, mul))


def _stage_latency_total(
    *,
    execution_latency_ms: int,
    snapshot_to_decision_ms: int | None,
    decision_to_submission_ms: int | None,
    submission_to_inclusion_ms: int | None,
) -> tuple[int, int, int, int]:
    if (
        snapshot_to_decision_ms is None
        and decision_to_submission_ms is None
        and submission_to_inclusion_ms is None
    ):
        total = max(0, int(execution_latency_ms))
        return 0, 0, total, total

    s2d = max(0, int(snapshot_to_decision_ms or 0))
    d2s = max(0, int(decision_to_submission_ms or 0))
    s2i = max(0, int(submission_to_inclusion_ms or 0))
    total = s2d + d2s + s2i
    return s2d, d2s, s2i, total


def _dynamic_latency_haircut(base_latency_haircut_pct: float, s2d_ms: int, d2s_ms: int, s2i_ms: int, total_ms: int) -> float:
    # Longer staged latency means worse queue position and higher stale risk.
    stage_penalty = (s2d_ms / 20000.0) + (d2s_ms / 16000.0) + (s2i_ms / 12000.0)
    total_penalty = total_ms / 30000.0
    return _clamp_pct(float(base_latency_haircut_pct) + stage_penalty + total_penalty)


def _apply_entry_drift(asks: list[dict[str, float]], steps: int) -> list[dict[str, float]]:
    if steps <= 0:
        return [dict(level) for level in asks]

    drifted: list[dict[str, float]] = []
    for idx, level in enumerate(asks):
        if idx > 0 and steps >= 2 and ((idx + steps) % 4 == 0):
            continue

        raw_price = float(level.get("price", 0.0))
        raw_tokens = float(level.get("token_amount", 0.0))
        raw_xrp = float(level.get("xrp_value", 0.0))
        if raw_price <= 0 or raw_tokens <= 0 or raw_xrp <= 0:
            continue

        price_widen = 1.0 + (0.0015 * steps) + (0.0003 * idx * steps)
        size_shrink = max(0.0, 1.0 - (0.09 * steps) - (0.015 * idx))
        drifted_tokens = raw_tokens * size_shrink
        drifted_xrp = raw_xrp * size_shrink
        drifted.append(
            {
                "price": raw_price * price_widen,
                "token_amount": drifted_tokens,
                "xrp_value": drifted_xrp,
            }
        )
    return drifted


def _apply_exit_drift(bids: list[dict[str, float]], steps: int) -> list[dict[str, float]]:
    if steps <= 0:
        return [dict(level) for level in bids]

    drifted: list[dict[str, float]] = []
    for idx, level in enumerate(bids):
        if idx > 0 and steps >= 2 and ((idx + steps) % 4 == 0):
            continue

        raw_price = float(level.get("price", 0.0))
        raw_tokens = float(level.get("token_amount", 0.0))
        raw_xrp = float(level.get("xrp_value", 0.0))
        if raw_price <= 0 or raw_tokens <= 0 or raw_xrp <= 0:
            continue

        price_deterioration = max(0.000001, 1.0 - (0.0015 * steps) - (0.0003 * idx * steps))
        size_shrink = max(0.0, 1.0 - (0.09 * steps) - (0.015 * idx))
        drifted_tokens = raw_tokens * size_shrink
        drifted_xrp = raw_xrp * size_shrink
        drifted.append(
            {
                "price": raw_price * price_deterioration,
                "token_amount": drifted_tokens,
                "xrp_value": drifted_xrp,
            }
        )
    return drifted


def _snapshot_age_ms(snapshot_time: datetime, signal_time: datetime, execution_latency_ms: int) -> tuple[int, datetime]:
    snap = _utc(snapshot_time)
    sig = _utc(signal_time)
    execution_time = sig + timedelta(milliseconds=max(0, execution_latency_ms))
    age_ms = int((execution_time - snap).total_seconds() * 1000.0)
    return max(0, age_ms), execution_time


def _fundedness_reliability_haircut(levels: list[dict[str, float]], side: str, idx: int) -> float:
    # XRPL offers can be partially funded. Treat highly concentrated top levels as less reliable.
    if idx != 0:
        return 0.0

    if side == "ask":
        total_visible = sum(max(0.0, float(level.get("xrp_value", 0.0))) for level in levels)
        top_visible = max(0.0, float(levels[0].get("xrp_value", 0.0))) if levels else 0.0
    else:
        total_visible = sum(max(0.0, float(level.get("token_amount", 0.0) * level.get("price", 0.0))) for level in levels)
        top_visible = max(0.0, float(levels[0].get("token_amount", 0.0) * levels[0].get("price", 0.0))) if levels else 0.0

    if total_visible <= 0:
        return 0.0

    top_share = top_visible / total_visible
    if top_share <= 0.70:
        return 0.0

    return min(0.60, max(0.0, (top_share - 0.70) * 1.5))


def simulate_entry_buy(
    *,
    asks: list[dict[str, float]],
    best_bid: float,
    best_ask: float,
    requested_size_xrp: float,
    snapshot_time: datetime,
    signal_time: datetime,
    execution_latency_ms: int,
    snapshot_to_decision_ms: int | None = None,
    decision_to_submission_ms: int | None = None,
    submission_to_inclusion_ms: int | None = None,
    max_snapshot_age_ms: int,
    liquidity_haircut_pct: float,
    latency_haircut_pct: float = 0.0,
    contention_haircut_pct: float = 0.0,
    trustline_liquidity_discount_pct: float = 0.0,
    ledger_drift_pct: float = 0.0,
    execution_window_snapshots: int = 0,
    min_level_xrp: float = 0.0,
    max_levels: int | None = None,
) -> ExecutionResult:
    requested = max(0.0, float(requested_size_xrp))
    s2d_ms, d2s_ms, s2i_ms, total_latency_ms = _stage_latency_total(
        execution_latency_ms=execution_latency_ms,
        snapshot_to_decision_ms=snapshot_to_decision_ms,
        decision_to_submission_ms=decision_to_submission_ms,
        submission_to_inclusion_ms=submission_to_inclusion_ms,
    )
    age_ms, _ = _snapshot_age_ms(snapshot_time, signal_time, total_latency_ms)
    if age_ms > max_snapshot_age_ms:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=total_latency_ms,
            snapshot_to_decision_ms=s2d_ms,
            decision_to_submission_ms=d2s_ms,
            submission_to_inclusion_ms=s2i_ms,
            total_execution_latency_ms=total_latency_ms,
            execution_window_snapshots=max(0, int(execution_window_snapshots)),
            drifted_best_bid=best_bid if best_bid > 0 else None,
            drifted_best_ask=best_ask if best_ask > 0 else None,
            failure_reason="STALE_MARKET_DATA",
            snapshot_age_ms=age_ms,
            queue_haircut_pct=_clamp_pct(liquidity_haircut_pct),
            latency_haircut_pct=_clamp_pct(latency_haircut_pct),
            contention_haircut_pct=_clamp_pct(contention_haircut_pct),
            trustline_liquidity_discount_pct=_clamp_pct(trustline_liquidity_discount_pct),
            ledger_drift_pct=_clamp_pct(ledger_drift_pct),
            effective_liquidity_ratio=0.0,
            fill_levels=[],
            consumed_levels_detailed=[],
        )

    if requested <= 0:
        return ExecutionResult(
            requested_size=0.0,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=total_latency_ms,
            snapshot_to_decision_ms=s2d_ms,
            decision_to_submission_ms=d2s_ms,
            submission_to_inclusion_ms=s2i_ms,
            total_execution_latency_ms=total_latency_ms,
            execution_window_snapshots=max(0, int(execution_window_snapshots)),
            drifted_best_bid=best_bid if best_bid > 0 else None,
            drifted_best_ask=best_ask if best_ask > 0 else None,
            failure_reason="NO_REQUESTED_SIZE",
            snapshot_age_ms=age_ms,
            queue_haircut_pct=_clamp_pct(liquidity_haircut_pct),
            latency_haircut_pct=_clamp_pct(latency_haircut_pct),
            contention_haircut_pct=_clamp_pct(contention_haircut_pct),
            trustline_liquidity_discount_pct=_clamp_pct(trustline_liquidity_discount_pct),
            ledger_drift_pct=_clamp_pct(ledger_drift_pct),
            effective_liquidity_ratio=0.0,
            fill_levels=[],
            consumed_levels_detailed=[],
        )

    if not asks or best_bid <= 0 or best_ask <= 0 or best_bid >= best_ask:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=total_latency_ms,
            snapshot_to_decision_ms=s2d_ms,
            decision_to_submission_ms=d2s_ms,
            submission_to_inclusion_ms=s2i_ms,
            total_execution_latency_ms=total_latency_ms,
            execution_window_snapshots=max(0, int(execution_window_snapshots)),
            drifted_best_bid=best_bid if best_bid > 0 else None,
            drifted_best_ask=best_ask if best_ask > 0 else None,
            failure_reason="INVALID_ORDERBOOK",
            snapshot_age_ms=age_ms,
            queue_haircut_pct=_clamp_pct(liquidity_haircut_pct),
            latency_haircut_pct=_clamp_pct(latency_haircut_pct),
            contention_haircut_pct=_clamp_pct(contention_haircut_pct),
            trustline_liquidity_discount_pct=_clamp_pct(trustline_liquidity_discount_pct),
            ledger_drift_pct=_clamp_pct(ledger_drift_pct),
            effective_liquidity_ratio=0.0,
            fill_levels=[],
            consumed_levels_detailed=[],
        )

    drift_steps = max(0, int(execution_window_snapshots))
    drifted_asks = _apply_entry_drift(asks, drift_steps)
    drifted_best_bid = best_bid
    drifted_best_ask = float(drifted_asks[0].get("price", 0.0)) if drifted_asks else 0.0

    queue_haircut = _clamp_pct(liquidity_haircut_pct)
    latency_haircut = _dynamic_latency_haircut(latency_haircut_pct, s2d_ms, d2s_ms, s2i_ms, total_latency_ms)
    contention_haircut = _clamp_pct(contention_haircut_pct)
    trustline_haircut = _clamp_pct(trustline_liquidity_discount_pct)
    ledger_drift_haircut = _clamp_pct(ledger_drift_pct)
    remaining_xrp = requested
    spent_xrp = 0.0
    tokens_bought = 0.0
    levels_used: list[dict[str, float | int]] = []
    raw_total_xrp = 0.0
    effective_total_xrp = 0.0

    for idx, level in enumerate(drifted_asks):
        if max_levels is not None and idx >= max_levels:
            break

        price = float(level.get("price", 0.0))
        raw_xrp_value = float(level.get("xrp_value", 0.0))
        raw_token_amount = float(level.get("token_amount", 0.0))
        raw_total_xrp += max(0.0, raw_xrp_value)
        fundedness_haircut = _fundedness_reliability_haircut(asks, "ask", idx)
        eff_mul = _degradation_multiplier(
            queue=queue_haircut,
            latency=latency_haircut,
            contention=contention_haircut,
            trustline=trustline_haircut,
            fundedness=fundedness_haircut,
            drift=ledger_drift_haircut,
        )
        effective_xrp_value = raw_xrp_value * eff_mul
        effective_token_amount = raw_token_amount * eff_mul
        effective_total_xrp += max(0.0, effective_xrp_value)
        if price <= 0 or effective_xrp_value <= 0 or effective_token_amount <= 0:
            continue
        if effective_xrp_value < max(0.0, float(min_level_xrp)):
            continue

        take_xrp = min(remaining_xrp, effective_xrp_value)
        token_take = (take_xrp / effective_xrp_value) * effective_token_amount
        spent_xrp += take_xrp
        tokens_bought += token_take
        levels_used.append(
            {
                "level_index": idx,
                "side": "ask",
                "price": price,
                "raw_liquidity_xrp": raw_xrp_value,
                "effective_liquidity_xrp": effective_xrp_value,
                "raw_tokens": raw_token_amount,
                "effective_tokens": effective_token_amount,
                "fundedness_haircut_pct": fundedness_haircut,
                "latency_haircut_pct": latency_haircut,
                "contention_haircut_pct": contention_haircut,
                "trustline_haircut_pct": trustline_haircut,
                "ledger_drift_pct": ledger_drift_haircut,
                "consumed_xrp": take_xrp,
                "consumed_tokens": token_take,
            }
        )
        remaining_xrp -= take_xrp
        if remaining_xrp <= 0:
            break

    eff_ratio = 0.0 if raw_total_xrp <= 0 else max(0.0, min(1.0, effective_total_xrp / raw_total_xrp))
    if spent_xrp <= 0 or tokens_bought <= 0:
        reason = "BOOK_COLLAPSED" if raw_total_xrp > 0 and eff_ratio < 0.25 else "NO_LIQUIDITY"
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=total_latency_ms,
            snapshot_to_decision_ms=s2d_ms,
            decision_to_submission_ms=d2s_ms,
            submission_to_inclusion_ms=s2i_ms,
            total_execution_latency_ms=total_latency_ms,
            execution_window_snapshots=drift_steps,
            drifted_best_bid=drifted_best_bid if drifted_best_bid > 0 else None,
            drifted_best_ask=drifted_best_ask if drifted_best_ask > 0 else None,
            failure_reason=reason,
            snapshot_age_ms=age_ms,
            queue_haircut_pct=queue_haircut,
            latency_haircut_pct=latency_haircut,
            contention_haircut_pct=contention_haircut,
            trustline_liquidity_discount_pct=trustline_haircut,
            ledger_drift_pct=ledger_drift_haircut,
            effective_liquidity_ratio=eff_ratio,
            fill_levels=[],
            consumed_levels_detailed=[],
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
        reason = "INSUFFICIENT_DEPTH"

    return ExecutionResult(
        requested_size=requested,
        filled_size=spent_xrp,
        avg_entry_price=avg_entry,
        avg_exit_price=None,
        fill_status=status,
        slippage_pct=slippage,
        execution_latency_ms=total_latency_ms,
        snapshot_to_decision_ms=s2d_ms,
        decision_to_submission_ms=d2s_ms,
        submission_to_inclusion_ms=s2i_ms,
        total_execution_latency_ms=total_latency_ms,
        execution_window_snapshots=drift_steps,
        drifted_best_bid=drifted_best_bid if drifted_best_bid > 0 else None,
        drifted_best_ask=drifted_best_ask if drifted_best_ask > 0 else None,
        failure_reason=reason,
        snapshot_age_ms=age_ms,
        queue_haircut_pct=queue_haircut,
        latency_haircut_pct=latency_haircut,
        contention_haircut_pct=contention_haircut,
        trustline_liquidity_discount_pct=trustline_haircut,
        ledger_drift_pct=ledger_drift_haircut,
        effective_liquidity_ratio=eff_ratio,
        fill_levels=levels_used,
        consumed_levels_detailed=levels_used,
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
    snapshot_to_decision_ms: int | None = None,
    decision_to_submission_ms: int | None = None,
    submission_to_inclusion_ms: int | None = None,
    max_snapshot_age_ms: int,
    liquidity_haircut_pct: float,
    latency_haircut_pct: float = 0.0,
    contention_haircut_pct: float = 0.0,
    trustline_liquidity_discount_pct: float = 0.0,
    ledger_drift_pct: float = 0.0,
    execution_window_snapshots: int = 0,
    min_level_xrp: float = 0.0,
    max_levels: int | None = None,
) -> ExecutionResult:
    requested = max(0.0, float(requested_token_size))
    s2d_ms, d2s_ms, s2i_ms, total_latency_ms = _stage_latency_total(
        execution_latency_ms=execution_latency_ms,
        snapshot_to_decision_ms=snapshot_to_decision_ms,
        decision_to_submission_ms=decision_to_submission_ms,
        submission_to_inclusion_ms=submission_to_inclusion_ms,
    )
    age_ms, _ = _snapshot_age_ms(snapshot_time, signal_time, total_latency_ms)
    if age_ms > max_snapshot_age_ms:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=total_latency_ms,
            snapshot_to_decision_ms=s2d_ms,
            decision_to_submission_ms=d2s_ms,
            submission_to_inclusion_ms=s2i_ms,
            total_execution_latency_ms=total_latency_ms,
            execution_window_snapshots=max(0, int(execution_window_snapshots)),
            drifted_best_bid=best_bid if best_bid > 0 else None,
            drifted_best_ask=best_ask if best_ask > 0 else None,
            failure_reason="STALE_MARKET_DATA",
            snapshot_age_ms=age_ms,
            queue_haircut_pct=_clamp_pct(liquidity_haircut_pct),
            latency_haircut_pct=_clamp_pct(latency_haircut_pct),
            contention_haircut_pct=_clamp_pct(contention_haircut_pct),
            trustline_liquidity_discount_pct=_clamp_pct(trustline_liquidity_discount_pct),
            ledger_drift_pct=_clamp_pct(ledger_drift_pct),
            effective_liquidity_ratio=0.0,
            fill_levels=[],
            consumed_levels_detailed=[],
        )

    if requested <= 0:
        return ExecutionResult(
            requested_size=0.0,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=total_latency_ms,
            snapshot_to_decision_ms=s2d_ms,
            decision_to_submission_ms=d2s_ms,
            submission_to_inclusion_ms=s2i_ms,
            total_execution_latency_ms=total_latency_ms,
            execution_window_snapshots=max(0, int(execution_window_snapshots)),
            drifted_best_bid=best_bid if best_bid > 0 else None,
            drifted_best_ask=best_ask if best_ask > 0 else None,
            failure_reason="NO_REQUESTED_SIZE",
            snapshot_age_ms=age_ms,
            queue_haircut_pct=_clamp_pct(liquidity_haircut_pct),
            latency_haircut_pct=_clamp_pct(latency_haircut_pct),
            contention_haircut_pct=_clamp_pct(contention_haircut_pct),
            trustline_liquidity_discount_pct=_clamp_pct(trustline_liquidity_discount_pct),
            ledger_drift_pct=_clamp_pct(ledger_drift_pct),
            effective_liquidity_ratio=0.0,
            fill_levels=[],
            consumed_levels_detailed=[],
        )

    if not bids or best_bid <= 0 or best_ask <= 0 or best_bid >= best_ask:
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=total_latency_ms,
            snapshot_to_decision_ms=s2d_ms,
            decision_to_submission_ms=d2s_ms,
            submission_to_inclusion_ms=s2i_ms,
            total_execution_latency_ms=total_latency_ms,
            execution_window_snapshots=max(0, int(execution_window_snapshots)),
            drifted_best_bid=best_bid if best_bid > 0 else None,
            drifted_best_ask=best_ask if best_ask > 0 else None,
            failure_reason="NO_BIDS",
            snapshot_age_ms=age_ms,
            queue_haircut_pct=_clamp_pct(liquidity_haircut_pct),
            latency_haircut_pct=_clamp_pct(latency_haircut_pct),
            contention_haircut_pct=_clamp_pct(contention_haircut_pct),
            trustline_liquidity_discount_pct=_clamp_pct(trustline_liquidity_discount_pct),
            ledger_drift_pct=_clamp_pct(ledger_drift_pct),
            effective_liquidity_ratio=0.0,
            fill_levels=[],
            consumed_levels_detailed=[],
        )

    drift_steps = max(0, int(execution_window_snapshots))
    drifted_bids = _apply_exit_drift(bids, drift_steps)
    drifted_best_bid = float(drifted_bids[0].get("price", 0.0)) if drifted_bids else 0.0
    drifted_best_ask = best_ask

    queue_haircut = _clamp_pct(liquidity_haircut_pct)
    latency_haircut = _dynamic_latency_haircut(latency_haircut_pct, s2d_ms, d2s_ms, s2i_ms, total_latency_ms)
    contention_haircut = _clamp_pct(contention_haircut_pct)
    trustline_haircut = _clamp_pct(trustline_liquidity_discount_pct)
    ledger_drift_haircut = _clamp_pct(ledger_drift_pct)
    remaining_tokens = requested
    sold_tokens = 0.0
    proceeds_xrp = 0.0
    levels_used: list[dict[str, float | int]] = []
    raw_total_xrp = 0.0
    effective_total_xrp = 0.0

    for idx, level in enumerate(drifted_bids):
        if max_levels is not None and idx >= max_levels:
            break

        price = float(level.get("price", 0.0))
        raw_token_amount = float(level.get("token_amount", 0.0))
        fundedness_haircut = _fundedness_reliability_haircut(bids, "bid", idx)
        eff_mul = _degradation_multiplier(
            queue=queue_haircut,
            latency=latency_haircut,
            contention=contention_haircut,
            trustline=trustline_haircut,
            fundedness=fundedness_haircut,
            drift=ledger_drift_haircut,
        )
        effective_token_amount = raw_token_amount * eff_mul
        raw_liquidity_xrp = raw_token_amount * price
        effective_liquidity_xrp = effective_token_amount * price
        raw_total_xrp += max(0.0, raw_liquidity_xrp)
        effective_total_xrp += max(0.0, effective_liquidity_xrp)
        if price <= 0 or effective_token_amount <= 0:
            continue
        if effective_liquidity_xrp < max(0.0, float(min_level_xrp)):
            continue

        take_tokens = min(remaining_tokens, effective_token_amount)
        proceeds_xrp += take_tokens * price
        sold_tokens += take_tokens
        levels_used.append(
            {
                "level_index": idx,
                "side": "bid",
                "price": price,
                "raw_liquidity_xrp": raw_liquidity_xrp,
                "effective_liquidity_xrp": effective_liquidity_xrp,
                "raw_tokens": raw_token_amount,
                "effective_tokens": effective_token_amount,
                "fundedness_haircut_pct": fundedness_haircut,
                "latency_haircut_pct": latency_haircut,
                "contention_haircut_pct": contention_haircut,
                "trustline_haircut_pct": trustline_haircut,
                "ledger_drift_pct": ledger_drift_haircut,
                "consumed_tokens": take_tokens,
                "proceeds_xrp": take_tokens * price,
            }
        )
        remaining_tokens -= take_tokens
        if remaining_tokens <= 0:
            break

    eff_ratio = 0.0 if raw_total_xrp <= 0 else max(0.0, min(1.0, effective_total_xrp / raw_total_xrp))
    if sold_tokens <= 0:
        reason = "BOOK_COLLAPSED" if raw_total_xrp > 0 and eff_ratio < 0.25 else "NO_BIDS"
        return ExecutionResult(
            requested_size=requested,
            filled_size=0.0,
            avg_entry_price=None,
            avg_exit_price=None,
            fill_status="UNFILLED",
            slippage_pct=None,
            execution_latency_ms=total_latency_ms,
            snapshot_to_decision_ms=s2d_ms,
            decision_to_submission_ms=d2s_ms,
            submission_to_inclusion_ms=s2i_ms,
            total_execution_latency_ms=total_latency_ms,
            execution_window_snapshots=drift_steps,
            drifted_best_bid=drifted_best_bid if drifted_best_bid > 0 else None,
            drifted_best_ask=drifted_best_ask if drifted_best_ask > 0 else None,
            failure_reason=reason,
            snapshot_age_ms=age_ms,
            queue_haircut_pct=queue_haircut,
            latency_haircut_pct=latency_haircut,
            contention_haircut_pct=contention_haircut,
            trustline_liquidity_discount_pct=trustline_haircut,
            ledger_drift_pct=ledger_drift_haircut,
            effective_liquidity_ratio=eff_ratio,
            fill_levels=[],
            consumed_levels_detailed=[],
        )

    avg_exit = proceeds_xrp / sold_tokens
    slippage: float | None = None
    if best_bid > 0:
        slippage = max(0.0, ((best_bid - avg_exit) / best_bid) * 100.0)
    status = _fill_status(requested, sold_tokens)
    reason = "INSUFFICIENT_DEPTH" if status == "PARTIAL" else None

    return ExecutionResult(
        requested_size=requested,
        filled_size=sold_tokens,
        avg_entry_price=None,
        avg_exit_price=avg_exit,
        fill_status=status,
        slippage_pct=slippage,
        execution_latency_ms=total_latency_ms,
        snapshot_to_decision_ms=s2d_ms,
        decision_to_submission_ms=d2s_ms,
        submission_to_inclusion_ms=s2i_ms,
        total_execution_latency_ms=total_latency_ms,
        execution_window_snapshots=drift_steps,
        drifted_best_bid=drifted_best_bid if drifted_best_bid > 0 else None,
        drifted_best_ask=drifted_best_ask if drifted_best_ask > 0 else None,
        failure_reason=reason,
        snapshot_age_ms=age_ms,
        queue_haircut_pct=queue_haircut,
        latency_haircut_pct=latency_haircut,
        contention_haircut_pct=contention_haircut,
        trustline_liquidity_discount_pct=trustline_haircut,
        ledger_drift_pct=ledger_drift_haircut,
        effective_liquidity_ratio=eff_ratio,
        fill_levels=levels_used,
        consumed_levels_detailed=levels_used,
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
