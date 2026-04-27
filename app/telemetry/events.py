from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TelemetryEvent:
    request_id: str
    event_type: str
    strategy: str
    token: str
    risk_decision: str
    execution_result: str
