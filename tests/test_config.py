from app.config import BotMode, Settings


def test_config_defaults_to_paper_mode() -> None:
    settings = Settings()
    assert settings.BOT_MODE == BotMode.PAPER_TRADING


def test_live_trading_disabled_by_default() -> None:
    settings = Settings()
    assert settings.LIVE_TRADING_ENABLED is False
    assert settings.EXECUTION_ENABLED is False


def test_wallet_seed_not_required_for_paper_mode() -> None:
    settings = Settings(XRPL_WALLET_SEED=None)
    assert settings.has_wallet_seed is False
    assert settings.BOT_MODE == BotMode.PAPER_TRADING
