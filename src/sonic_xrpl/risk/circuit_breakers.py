"""Circuit breakers for the risk layer."""

from __future__ import annotations

from dataclasses import dataclass

from sonic_xrpl.core.modes import RuntimeMode


@dataclass
class CircuitBreaker:
    """A single circuit breaker that can trip to halt execution."""

    name: str
    is_tripped: bool
    reason: str


def check_circuit_breakers(mode: RuntimeMode) -> list[CircuitBreaker]:
    """Check all circuit breakers for the given mode.

    Returns a list of CircuitBreaker objects.
    Any with is_tripped=True should halt execution.
    """
    breakers: list[CircuitBreaker] = []

    # Live trading circuit breaker — always tripped in Phase 45
    breakers.append(
        CircuitBreaker(
            name="live_trading_disabled",
            is_tripped=(mode == RuntimeMode.LIVE),
            reason="Live trading is disabled in Phase 45",
        )
    )

    # Submission circuit breaker — always tripped regardless of mode
    breakers.append(
        CircuitBreaker(
            name="submission_disabled",
            is_tripped=True,
            reason="Transaction submission is unconditionally blocked in Phase 45",
        )
    )

    return breakers


def any_breaker_tripped(mode: RuntimeMode) -> bool:
    """Return True if any circuit breaker is tripped."""
    return any(cb.is_tripped for cb in check_circuit_breakers(mode))
