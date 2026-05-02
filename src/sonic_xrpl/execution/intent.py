"""Execution Intent model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from sonic_xrpl.core.modes import RuntimeMode


class IntentStatus(str, Enum):
    PENDING = "pending"
    RISK_APPROVED = "risk_approved"
    RISK_REJECTED = "risk_rejected"
    PLANNED = "planned"
    SIMULATED = "simulated"
    PAPER_EXECUTED = "paper_executed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionIntent:
    """An execution intent created by the strategy/risk pipeline.

    live_submission_allowed is ALWAYS False in Phase 45.
    """

    mode: RuntimeMode
    strategy_id: str
    asset_in: str
    asset_out: str
    amount: float
    max_slippage_bps: int = 100
    confidence: float = 0.5
    risk_evidence: dict = field(default_factory=dict)
    feature_requirements: list[str] = field(default_factory=list)
    status: IntentStatus = IntentStatus.PENDING
    intent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError(f"amount must be positive, got {self.amount}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be in [0, 1], got {self.confidence}"
            )
