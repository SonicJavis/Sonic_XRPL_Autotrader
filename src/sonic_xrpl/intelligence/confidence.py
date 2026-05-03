"""Confidence scoring for intelligence layer signals.

Produces a 0.0–1.0 confidence score from multiple contributing factors.
Intelligence does NOT execute (Architecture Rule #6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConfidenceScore:
    """A composite confidence score with contributing factor breakdown."""

    value: float
    components: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"ConfidenceScore.value must be in [0, 1], got {self.value}")


def compute_confidence(**factors: float) -> ConfidenceScore:
    """Compute a confidence score from named factor weights.

    Each factor should be in [0.0, 1.0].
    Returns the arithmetic mean of all provided factors.

    Example::

        score = compute_confidence(
            liquidity=0.8,
            spread=0.6,
            oracle_agreement=0.9,
        )
        assert 0.0 <= score.value <= 1.0
    """
    if not factors:
        return ConfidenceScore(value=0.5, notes=["no factors provided — using neutral 0.5"])

    for name, val in factors.items():
        if not 0.0 <= val <= 1.0:
            raise ValueError(f"Factor {name!r} must be in [0, 1], got {val}")

    avg = sum(factors.values()) / len(factors)
    return ConfidenceScore(
        value=round(avg, 4),
        components=dict(factors),
    )
