"""New-token scanner strategy — placeholder implementation.

Generates simulated BUY signals for demo / paper-trading purposes.
Real FirstLedger integration will replace this in a future phase.
"""

from __future__ import annotations

import random

from app.strategies.base import BaseStrategy, SignalPayload
from app.telemetry import get_logger

logger = get_logger("strategies.new_token_scanner")

# Placeholder tokens — replace with real FirstLedger feed later.
_DEMO_TOKENS = [
    ("SONIC", "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh"),
    ("MOON", "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe"),
    ("DOGE2", "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59"),
]


class NewTokenScannerStrategy(BaseStrategy):
    """Scans for newly listed tokens and generates BUY signals (simulated)."""

    name = "new_token_scanner"

    def generate_signal(self) -> SignalPayload | None:
        """Return a random simulated BUY signal, or None (50 % chance)."""
        if random.random() < 0.5:
            logger.debug("No signal this tick")
            return None

        currency, issuer = random.choice(_DEMO_TOKENS)
        price = round(random.uniform(0.001, 0.1), 6)
        signal = SignalPayload(
            strategy_name=self.name,
            currency=currency,
            issuer=issuer,
            direction="BUY",
            price_xrp=price,
            confidence=round(random.uniform(0.6, 1.0), 2),
            metadata={"source": "placeholder"},
        )
        logger.info(
            "Signal generated",
            strategy=self.name,
            currency=currency,
            direction="BUY",
            price_xrp=price,
        )
        return signal
