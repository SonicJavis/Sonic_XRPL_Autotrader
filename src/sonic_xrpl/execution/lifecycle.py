"""Execution Lifecycle — append-only event log for execution domain.

Architecture Rule #11: Execution lifecycle must be append-only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LifecycleEventType(str, Enum):
    INTENT_CREATED = "intent_created"
    PLAN_CREATED = "plan_created"
    RISK_CHECKED = "risk_checked"
    SIMULATED = "simulated"
    PAPER_EXECUTED = "paper_executed"
    CANCELLED = "cancelled"
    ERROR = "error"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LifecycleEvent:
    """A single immutable event in the execution lifecycle."""

    plan_id: str
    event_type: LifecycleEventType
    payload: dict[str, Any] = field(default_factory=dict)
    severity: Severity = Severity.INFO
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class LifecycleLog:
    """Append-only log of lifecycle events for a given plan.

    Architecture Rule #11: This log is append-only.
    Events cannot be removed or mutated after appending.
    """

    def __init__(self, plan_id: str) -> None:
        self._plan_id = plan_id
        self._events: list[LifecycleEvent] = []

    def append(self, event: LifecycleEvent) -> None:
        """Append a lifecycle event. Events cannot be removed."""
        if event.plan_id != self._plan_id:
            raise ValueError(
                f"Event plan_id {event.plan_id!r} does not match log plan_id {self._plan_id!r}"
            )
        self._events.append(event)

    def events(self) -> list[LifecycleEvent]:
        """Return a copy of all events (read-only)."""
        return list(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def add(
        self,
        event_type: LifecycleEventType,
        payload: dict[str, Any] | None = None,
        severity: Severity = Severity.INFO,
    ) -> LifecycleEvent:
        """Convenience method to create and append an event."""
        event = LifecycleEvent(
            plan_id=self._plan_id,
            event_type=event_type,
            payload=payload or {},
            severity=severity,
        )
        self.append(event)
        return event
