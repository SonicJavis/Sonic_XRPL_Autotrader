from app.models import Signal
from app.strategy import MeanReversionStrategy


def test_strategy_holds_while_warming_up() -> None:
    strategy = MeanReversionStrategy(symbol="XRP/USD", lookback=5)

    for _ in range(4):
        decision = strategy.update(0.5)

    assert decision.signal == Signal.HOLD
    assert decision.reason == "warming up"


def test_strategy_emits_buy_on_drop() -> None:
    strategy = MeanReversionStrategy(symbol="XRP/USD", lookback=5, z_buy=-0.5, z_sell=0.8)

    for px in [1.0, 1.0, 1.0, 1.0, 0.2]:
        decision = strategy.update(px)

    assert decision.signal == Signal.BUY
