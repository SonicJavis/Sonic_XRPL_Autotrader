from __future__ import annotations

import random
import time

from rich.console import Console

from .trader import build_default_trader


def main() -> None:
    console = Console()
    trader = build_default_trader()
    price = 0.50

    console.print("Starting XRPL autotrader scaffold loop. Press Ctrl+C to stop.")

    try:
        while True:
            price = max(0.0001, price + random.uniform(-0.02, 0.02))
            decision = trader.on_price(price)
            console.print(
                f"price={price:.4f} signal={decision.signal.value} confidence={decision.confidence:.2f}"
            )
            time.sleep(trader.settings.polling_interval_seconds)
    except KeyboardInterrupt:
        console.print("Stopped.")


if __name__ == "__main__":
    main()
