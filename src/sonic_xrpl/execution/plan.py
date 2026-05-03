"""Execution Plan model.

live_submission_allowed is hardcoded False in Phase 45.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class ExecutionPlan:
    """A concrete execution plan derived from a risk-approved intent.

    live_submission_allowed is unconditionally False in Phase 45.
    Any code that reads this field must not submit if it is False.
    """

    intent_id: str
    provider_hint: str = "mock"
    expected_fee: int = 12
    expected_slippage_bps: float = 0.0
    expected_ledger_latency: int = 4000
    route_summary: str = ""
    simulation_required: bool = True
    risk_approved: bool = False
    live_submission_allowed: bool = field(default=False, init=False)
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        # Ensure live_submission_allowed cannot be set to True in Phase 45
        object.__setattr__(self, "live_submission_allowed", False)
