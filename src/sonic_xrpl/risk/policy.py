"""Risk policy definitions.

Risk approves or rejects execution intent (Architecture Rule #8).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sonic_xrpl.core.modes import RuntimeMode


@dataclass
class RiskPolicy:
    """Configuration governing risk approval decisions."""

    max_slippage_bps: int = 100
    max_position_size: float = 1000.0
    min_confidence: float = 0.6
    allowed_modes: list[RuntimeMode] = field(
        default_factory=lambda: [RuntimeMode.SIMULATION, RuntimeMode.PAPER]
    )

    def is_mode_allowed(self, mode: RuntimeMode) -> bool:
        return mode in self.allowed_modes


DEFAULT_RISK_POLICY = RiskPolicy()
