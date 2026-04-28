from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class Token(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    issuer: str
    currency: str
    symbol: str
    source: str = "manual"
    created_at: datetime = Field(default_factory=utcnow)
    is_active: bool = True


class WatchedToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    issuer: str = ""
    currency: str
    is_xrp: bool = False
    first_seen_at: datetime = Field(default_factory=utcnow)
    last_seen_at: datetime = Field(default_factory=utcnow)
    is_active: bool = True


class MarketSnapshot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token_id: int | None = Field(default=None, foreign_key="watchedtoken.id")
    price_xrp: float | None = None
    liquidity_xrp: float = 0.0
    liquidity_bid_xrp: float = 0.0
    liquidity_ask_xrp: float = 0.0
    spread_pct: float | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    volume_estimate: float = 0.0
    tx_count: int = 0
    bid_count: int = 0
    ask_count: int = 0
    created_at: datetime = Field(default_factory=utcnow)


class MarketDepthLevel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    snapshot_id: int | None = Field(default=None, foreign_key="marketsnapshot.id")
    side: str
    level_index: int
    price_xrp_per_token: float
    token_amount: float
    xrp_value: float
    cumulative_xrp: float
    created_at: datetime = Field(default_factory=utcnow)


class Signal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    strategy_name: str
    issuer: str
    currency: str
    side: str
    confidence: float
    risk_score: float
    suggested_size_xrp: float
    reason: str
    created_at: datetime = Field(default_factory=utcnow)


class PaperTrade(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    issuer: str
    currency: str
    side: str
    entry_price_xrp: float
    exit_price_xrp: float | None = None
    size_xrp: float
    pnl_xrp: float = 0.0
    capital_reservation_id: int | None = Field(default=None, foreign_key="capitalreservation.id")
    status: str = "OPEN"
    opened_at: datetime = Field(default_factory=utcnow)
    closed_at: datetime | None = None


class CapitalLedger(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    available_balance_xrp: float
    locked_balance_xrp: float = 0.0
    total_balance_xrp: float
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class CapitalReservation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    signal_id: int | None = Field(default=None, foreign_key="signal.id", index=True)
    issuer: str
    currency: str
    reserved_xrp: float
    deployed_xrp: float = 0.0
    released_xrp: float = 0.0
    status: str = "ACTIVE"
    failure_reason: str | None = None
    trade_id: int | None = Field(default=None, foreign_key="papertrade.id")
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class PaperTradeOutcome(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    token_id: int = Field(foreign_key="watchedtoken.id", index=True)
    signal_id: int = Field(foreign_key="signal.id", index=True)
    snapshot_id: int | None = Field(default=None, foreign_key="marketsnapshot.id")

    entry_price: float
    expected_slippage_pct: float
    actual_slippage_pct: float | None = None

    target_size_xrp: float
    filled_size_xrp: float

    fill_success: bool
    partial_fill: bool
    fill_status: str = "UNFILLED"

    entry_time: datetime = Field(default_factory=utcnow)
    snapshot_time: datetime = Field(default_factory=utcnow)
    signal_time: datetime = Field(default_factory=utcnow)
    execution_time: datetime = Field(default_factory=utcnow)
    exit_time: datetime | None = None

    exit_price: float | None = None
    pnl_xrp: float | None = None

    max_adverse_excursion_pct: float = 0.0
    max_favorable_excursion_pct: float = 0.0

    execution_latency_ms: int = 0
    snapshot_age_ms: int = 0
    failure_reason: str | None = None

    reason_closed: str | None = None
    legacy_only: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class Position(SQLModel, table=True):
    position_id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)

    issuer: str
    currency: str
    token_id: int = Field(foreign_key="watchedtoken.id", index=True)
    signal_id: int = Field(foreign_key="signal.id", index=True)
    risk_decision_id: int | None = Field(default=None, foreign_key="riskdecisionrecord.id")
    execution_id: int | None = Field(default=None, foreign_key="executionrecord.id")

    entry_time: datetime = Field(default_factory=utcnow)
    exit_time: datetime | None = None

    entry_vwap: float
    exit_vwap: float | None = None

    entry_filled_size: float
    exit_filled_size: float = 0.0
    remaining_size: float

    entry_orderbook_snapshot_id: int = Field(foreign_key="marketsnapshot.id")
    exit_orderbook_snapshot_id: int | None = Field(default=None, foreign_key="marketsnapshot.id")

    status: str = "OPEN"
    failure_reason: str | None = None
    exit_attempt_count: int = 0
    last_exit_attempt_time: datetime | None = None
    exit_failure_reason: str | None = None

    component_scores_json: str = "{}"
    risk_flags_json: str = "[]"
    execution_details_json: str = "{}"

    created_at: datetime = Field(default_factory=utcnow)


class ExecutionRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    token_id: int = Field(foreign_key="watchedtoken.id", index=True)
    signal_id: int = Field(foreign_key="signal.id", index=True)
    risk_decision_id: int | None = Field(default=None, foreign_key="riskdecisionrecord.id")
    snapshot_id: int = Field(foreign_key="marketsnapshot.id")
    position_id: str | None = Field(default=None, foreign_key="position.position_id")

    side: str
    requested_size: float
    filled_size: float
    fill_status: str
    avg_fill_price: float | None = None
    fill_levels_json: list[dict[str, float | int]] = Field(default_factory=list, sa_column=Column(JSON))
    slippage_vs_top: float | None = None

    snapshot_time: datetime = Field(default_factory=utcnow)
    signal_time: datetime = Field(default_factory=utcnow)
    execution_time: datetime = Field(default_factory=utcnow)
    execution_latency_ms: int = 0
    snapshot_age_ms: int = 0
    holding_time_ms: int = 0

    failure_reason: str | None = None
    execution_details_json: str = "{}"
    created_at: datetime = Field(default_factory=utcnow)


class PositionExitFill(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    position_id: str = Field(foreign_key="position.position_id", index=True)
    execution_id: int | None = Field(default=None, foreign_key="executionrecord.id")
    snapshot_id: int | None = Field(default=None, foreign_key="marketsnapshot.id")

    exit_time: datetime = Field(default_factory=utcnow)
    exit_vwap: float
    fill_size: float
    pnl_xrp: float
    fill_levels_json: list[dict[str, float | int]] = Field(default_factory=list, sa_column=Column(JSON))
    failure_reason: str | None = None

    created_at: datetime = Field(default_factory=utcnow)


class RiskEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    event_type: str
    severity: str
    reason: str
    created_at: datetime = Field(default_factory=utcnow)


class AlphaCooldownRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token_id: int = Field(foreign_key="watchedtoken.id", index=True)
    rejected_at: datetime = Field(default_factory=utcnow)


class RiskDecisionRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token_id: int | None = Field(default=None, foreign_key="watchedtoken.id")
    snapshot_id: int | None = Field(default=None, foreign_key="marketsnapshot.id")
    signal_id: int | None = Field(default=None, foreign_key="signal.id")
    decision: str
    reason: str
    score: float = 0.0
    reasons_json: str = "[]"
    created_at: datetime = Field(default_factory=utcnow)


class AlphaSignal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    token_id: int | None = Field(default=None, foreign_key="watchedtoken.id")
    snapshot_id: int | None = Field(default=None, foreign_key="marketsnapshot.id")
    pair: str
    score: float
    decision: str
    reasons_json: str
    spread_pct: float | None = None
    depth_xrp: float = 0.0
    imbalance: float = 0.0
    slippage_pct: float = 0.0
    fill_probability: float = 0.0
    stability_score: float = 0.0
    spread_stability: float = 0.0
    liquidity_consistency: float = 0.0
    mid_price_stability: float = 0.0
    component_scores_json: str = "{}"
    manipulation_flags_json: str = "{}"
    created_at: datetime = Field(default_factory=utcnow)


class AuditEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    request_id: str
    event_type: str
    payload_json: str
    created_at: datetime = Field(default_factory=utcnow)
