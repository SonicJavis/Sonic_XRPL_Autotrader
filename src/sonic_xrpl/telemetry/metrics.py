"""Telemetry metrics collector."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    name: str
    value: float
    metric_type: MetricType = MetricType.GAUGE
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


_metrics_store: list[Metric] = []


def record_metric(
    name: str,
    value: float,
    metric_type: MetricType = MetricType.GAUGE,
    tags: dict[str, str] | None = None,
) -> Metric:
    """Record a metric and store it in-memory."""
    m = Metric(name=name, value=value, metric_type=metric_type, tags=tags or {})
    _metrics_store.append(m)
    return m


def get_all_metrics() -> list[Metric]:
    """Return all recorded metrics."""
    return list(_metrics_store)


def clear_metrics() -> None:
    """Clear the in-memory metrics store."""
    _metrics_store.clear()
