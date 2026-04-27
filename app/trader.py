from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .models import Signal, TradeDecision
from .strategy import MeanReversionStrategy
from .xrpl_client import XRPLClient


@dataclass(slots=True)
class AutoTrader:
    settings: Settings
    strategy: MeanReversionStrategy
    client: XRPLClient

    def on_price(self, price: float) -> TradeDecision:
        decision = self.strategy.update(price)

        if decision.signal == Signal.BUY:
            self.client.submit_order(self.settings.trading_symbol, "buy", self.settings.trade_amount)
        elif decision.signal == Signal.SELL:
            self.client.submit_order(self.settings.trading_symbol, "sell", self.settings.trade_amount)

        return decision


def build_default_trader() -> AutoTrader:
    settings = Settings()
    strategy = MeanReversionStrategy(symbol=settings.trading_symbol)
    client = XRPLClient(network_url=settings.xrpl_network_url)
    return AutoTrader(settings=settings, strategy=strategy, client=client)
