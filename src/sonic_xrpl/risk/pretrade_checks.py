"""Pre-trade risk checks.

Risk approves or rejects execution intent (Architecture Rule #8).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sonic_xrpl.risk.policy import RiskPolicy, DEFAULT_RISK_POLICY

if TYPE_CHECKING:
    from sonic_xrpl.execution.intent import ExecutionIntent


@dataclass
class PreTradeCheckResult:
    """Result of running all pre-trade risk checks."""

    passed: bool
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run_pretrade_checks(
    intent: "ExecutionIntent",
    policy: RiskPolicy | None = None,
) -> PreTradeCheckResult:
    """Run pre-trade risk checks against the given policy.

    Returns PreTradeCheckResult with passed=True only if all checks pass.
    """
    policy = policy or DEFAULT_RISK_POLICY
    failures: list[str] = []
    warnings: list[str] = []

    if not policy.is_mode_allowed(intent.mode):
        failures.append(
            f"Mode {intent.mode.value!r} is not allowed by policy. "
            f"Allowed: {[m.value for m in policy.allowed_modes]}"
        )

    if intent.confidence < policy.min_confidence:
        failures.append(
            f"Confidence {intent.confidence:.3f} is below minimum {policy.min_confidence:.3f}"
        )

    if intent.max_slippage_bps > policy.max_slippage_bps:
        failures.append(
            f"max_slippage_bps {intent.max_slippage_bps} exceeds policy limit {policy.max_slippage_bps}"
        )

    if intent.amount > policy.max_position_size:
        warnings.append(
            f"amount {intent.amount} exceeds recommended max {policy.max_position_size}"
        )

    return PreTradeCheckResult(
        passed=len(failures) == 0,
        failures=failures,
        warnings=warnings,
    )
