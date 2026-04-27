"""Structured logging / telemetry helpers."""

from __future__ import annotations

import uuid
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)


def get_logger(name: str = "sonic_trader") -> structlog.BoundLogger:
    return structlog.get_logger(name)


def new_request_id() -> str:
    """Generate a unique request/trace ID."""
    return uuid.uuid4().hex[:12]
