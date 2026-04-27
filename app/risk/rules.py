from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.market_data.metrics import MarketMetrics


class RiskDecision(str, Enum):
    APPROVE = "APPROVE"
    DENY = "DENY"
    REDUCE_SIZE = "REDUCE_SIZE"
    REQUIRE_MANUAL_APPROVAL = "REQUIRE_MANUAL_APPROVAL"


@dataclass(slots=True)
class RiskContext:
    open_positions: int
    total_exposure_xrp: float
    daily_loss_xrp: float
    market_snapshot: MarketMetrics | None = None
    bid_count: int = 0
    ask_count: int = 0
    bids: list[dict[str, float]] | None = None
    asks: list[dict[str, float]] | None = None
    slippage_pct: float | None = None
    fill_possible: bool = True
    is_exit: bool = False
    live_trading_requested: bool = False


@dataclass(slots=True)
class RiskEvaluation:
    decision: RiskDecision
    reason: str
    approved_size_xrp: float
