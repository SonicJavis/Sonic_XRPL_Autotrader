from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class XRPLClient:
    network_url: str

    def submit_order(self, symbol: str, side: str, amount: float) -> dict[str, str | float]:
        # Placeholder implementation for scaffold phase.
        return {
            "status": "submitted",
            "network_url": self.network_url,
            "symbol": symbol,
            "side": side,
            "amount": amount,
        }
