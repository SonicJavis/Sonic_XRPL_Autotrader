"""System event model for Sonic XRPL V2."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Typed event kinds emitted by the V2 system."""

    INTENT_CREATED = "intent_created"
    PLAN_CREATED = "plan_created"
    SIMULATION_RUN = "simulation_run"
    PAPER_EXECUTED = "paper_executed"
    RISK_APPROVED = "risk_approved"
    RISK_REJECTED = "risk_rejected"
    AUDIT_RUN = "audit_run"
    SAFETY_SCAN_RUN = "safety_scan_run"
    PROVIDER_HEALTH_CHECK = "provider_health_check"
    CAPABILITY_QUERIED = "capability_queried"
    MODE_CHANGED = "mode_changed"
    ERROR = "error"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemEvent:
    """Immutable event emitted by the V2 system."""

    event_type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    severity: Severity = Severity.INFO
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
