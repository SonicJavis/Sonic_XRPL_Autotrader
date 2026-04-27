from app.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.trading_symbol == "XRP/USD"
    assert settings.trade_amount > 0
