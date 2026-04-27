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


class RiskEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    event_type: str
    severity: str
    reason: str
    created_at: datetime = Field(default_factory=utcnow)


class AuditEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    request_id: str
    event_type: str
    payload_json: str
    created_at: datetime = Field(default_factory=utcnow)
