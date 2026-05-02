"""Paper execution engine.

Records paper trades without network submission.
Paper trading requires mode=PAPER (enforced via live_guard).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sonic_xrpl.core.modes import RuntimeMode
from sonic_xrpl.execution.live_guard import assert_can_paper_trade
from sonic_xrpl.execution.plan import ExecutionPlan
from sonic_xrpl.simulation.fill_model import FillEstimate


@dataclass
class PaperExecutionRecord:
    """Record of a paper execution."""

    plan_id: str
    simulated_fill: float
    paper_fill: float
    delta: float = 0.0
    notes: str = ""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        self.delta = self.paper_fill - self.simulated_fill


class PaperExecutor:
    """Executes paper trades, recording outcomes without live submission."""

    def __init__(self, mode: RuntimeMode = RuntimeMode.PAPER) -> None:
        self._mode = mode
        self._records: list[PaperExecutionRecord] = []

    def execute_paper(
        self,
        plan: ExecutionPlan,
        simulation: FillEstimate,
        notes: str = "",
    ) -> PaperExecutionRecord:
        """Execute a paper trade from a plan and simulation estimate.

        Raises ModeViolationError if not in PAPER mode.
        Never submits to the network.
        """
        assert_can_paper_trade(self._mode)

        # Paper fill = simulation fill with a small realistic variance placeholder
        # Future phases will add more realistic paper fill models
        paper_fill_pct = simulation.expected_fill_pct * 0.98  # conservative 2% discount

        record = PaperExecutionRecord(
            plan_id=plan.plan_id,
            simulated_fill=simulation.expected_fill_pct,
            paper_fill=round(paper_fill_pct, 4),
            notes=notes or f"Paper trade for plan {plan.plan_id}",
        )
        self._records.append(record)
        return record

    def get_records(self) -> list[PaperExecutionRecord]:
        """Return all paper execution records."""
        return list(self._records)
