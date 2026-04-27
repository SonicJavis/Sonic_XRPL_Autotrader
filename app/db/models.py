from __future__ import annotations

from datetime import datetime, timezone

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
    status: str = "OPEN"
    opened_at: datetime = Field(default_factory=utcnow)
    closed_at: datetime | None = None


class PaperTradeOutcome(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    token_id: int = Field(foreign_key="watchedtoken.id", index=True)
    signal_id: int = Field(foreign_key="signal.id", index=True)
    snapshot_id: int | None = Field(default=None, foreign_key="marketsnapshot.id")

    entry_price: float
    expected_slippage_pct: float
    actual_slippage_pct: float

    target_size_xrp: float
    filled_size_xrp: float

    fill_success: bool
    partial_fill: bool

    entry_time: datetime = Field(default_factory=utcnow)
    exit_time: datetime | None = None

    exit_price: float | None = None
    pnl_xrp: float | None = None

    max_adverse_excursion_pct: float = 0.0
    max_favorable_excursion_pct: float = 0.0

    reason_closed: str | None = None
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
