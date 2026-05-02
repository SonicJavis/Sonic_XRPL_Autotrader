"""Slippage estimation for simulation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SlippageEstimate:
    """Estimated price slippage in basis points and percentage."""

    basis_points: float
    pct: float
    notes: str = ""

    def __post_init__(self) -> None:
        if self.basis_points < 0:
            raise ValueError(f"basis_points must be non-negative, got {self.basis_points}")


def estimate_slippage(
    amount: float,
    liquidity_score: float = 1.0,
) -> SlippageEstimate:
    """Estimate slippage for a trade of the given amount.

    Higher liquidity_score = lower slippage.
    Liquidity score should be in (0, 1].

    This is a deterministic linear model. Future phases will use
    AMM constant-product or orderbook depth for accuracy.

    Args:
        amount: Trade amount in asset units.
        liquidity_score: Normalised liquidity quality in (0, 1].

    Returns:
        SlippageEstimate with basis_points and pct.
    """
    if liquidity_score <= 0:
        liquidity_score = 0.01

    # Base slippage: 10 bps per unit of normalised amount pressure
    # Adjust by liquidity quality
    base_bps = 10.0 * (amount / 1000.0) / liquidity_score
    # Cap at 500 bps (5%) for the placeholder model
    bps = min(500.0, base_bps)

    return SlippageEstimate(
        basis_points=round(bps, 2),
        pct=round(bps / 10_000, 6),
        notes=f"Linear slippage model (amount={amount}, liquidity_score={liquidity_score})",
    )
