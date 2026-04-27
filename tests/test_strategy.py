from app.market_data.token_registry import RegisteredToken, TokenRegistry
from app.strategies.base import StrategyContext
from app.strategies.new_token_scanner import NewTokenScannerStrategy


def test_new_token_scanner_generates_buy_for_registered_token() -> None:
    registry = TokenRegistry()
    registry.register(RegisteredToken(issuer="rIssuer", currency="USD", symbol="TEST"))
    strategy = NewTokenScannerStrategy(token_registry=registry)

    signal = strategy.generate_signal(StrategyContext(current_price_xrp=1.0))

    assert signal is not None
    assert signal.side == "BUY"


def test_new_token_scanner_returns_none_without_tokens() -> None:
    strategy = NewTokenScannerStrategy(token_registry=TokenRegistry())

    signal = strategy.generate_signal(StrategyContext(current_price_xrp=1.0))

    assert signal is None
