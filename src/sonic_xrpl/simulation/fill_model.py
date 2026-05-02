"""Fill model — simulation of expected order fill.

Simulation must not assume guaranteed fills (Architecture Rule #10).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FillModelType(str, Enum):
    """Supported fill model types."""

    FIXED = "fixed"
    AMM_IMPACT = "amm_impact"
    ORDERBOOK_DEPTH = "orderbook_depth"


@dataclass
class FillEstimate:
    """Estimated fill outcome from the simulation model."""

    model_type: FillModelType
    expected_fill_pct: float
    notes: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.expected_fill_pct <= 1.0:
            raise ValueError(
                f"expected_fill_pct must be in [0, 1], got {self.expected_fill_pct}"
            )


def estimate_fill(
    amount: float,
    model_type: FillModelType = FillModelType.FIXED,
    **kwargs: float,
) -> FillEstimate:
    """Estimate fill percentage for the given amount and model type.

    This is a deterministic simulation — no guaranteed fills are assumed.

    Args:
        amount: Trade amount in asset units.
        model_type: Fill model to apply.
        **kwargs: Model-specific parameters.

    Returns:
        FillEstimate with expected_fill_pct in [0.0, 1.0].
    """
    if model_type == FillModelType.FIXED:
        # Fixed model: assume partial fill based on a conservative factor
        fill_factor = kwargs.get("fill_factor", 0.92)
        return FillEstimate(
            model_type=model_type,
            expected_fill_pct=min(1.0, max(0.0, fill_factor)),
            notes="Fixed fill model — conservative 92% expected fill",
        )

    if model_type == FillModelType.AMM_IMPACT:
        # AMM impact placeholder — future Phase 48 will implement proper constant-product math
        pool_size = kwargs.get("pool_size", 1_000_000.0)
        impact = amount / (pool_size + amount) if pool_size > 0 else 0.5
        fill_pct = max(0.0, 1.0 - impact)
        return FillEstimate(
            model_type=model_type,
            expected_fill_pct=round(fill_pct, 4),
            notes=f"AMM impact placeholder (pool_size={pool_size})",
        )

    if model_type == FillModelType.ORDERBOOK_DEPTH:
        # Orderbook depth placeholder — future Phase 48 will use real depth data
        available_liquidity = kwargs.get("available_liquidity", amount * 2)
        fill_pct = min(1.0, available_liquidity / amount) if amount > 0 else 0.0
        return FillEstimate(
            model_type=model_type,
            expected_fill_pct=round(fill_pct, 4),
            notes=f"Orderbook depth placeholder (available={available_liquidity})",
        )

    return FillEstimate(
        model_type=model_type,
        expected_fill_pct=0.9,
        notes="Unknown model type — using conservative fallback",
    )
