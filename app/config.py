from __future__ import annotations

from enum import Enum

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotMode(str, Enum):
    PAPER_TRADING = "PAPER_TRADING"
    SCANNER_ONLY = "SCANNER_ONLY"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_MODE: BotMode = BotMode.PAPER_TRADING
    LIVE_TRADING_ENABLED: bool = False
    ALLOW_REMOTE_ACCESS: bool = False

    XRPL_RPC_URL: str = "https://s1.ripple.com:51234"
    XRPL_WS_URL: str = "wss://s1.ripple.com"
    XRPL_WALLET_SEED: SecretStr | None = Field(default=None, repr=False)

    MAX_TRADE_XRP: float = Field(default=5.0, gt=0)
    MAX_OPEN_POSITIONS: int = Field(default=3, ge=1)
    MAX_TOTAL_EXPOSURE_XRP: float = Field(default=20.0, gt=0)
    MAX_DAILY_LOSS_XRP: float = Field(default=10.0, gt=0)
    MIN_LIQUIDITY_XRP: float = Field(default=1000.0, ge=0)
    MAX_SPREAD_PCT: float = Field(default=8.0, ge=0)
    MAX_SLIPPAGE_PCT: float = Field(default=5.0, ge=0)

    DEFAULT_STOPLOSS_PCT: float = Field(default=10.0, ge=0)
    DEFAULT_TAKE_PROFIT_PCT: float = Field(default=20.0, ge=0)

    PAPER_STARTING_BALANCE_XRP: float = Field(default=1000.0, ge=0)

    DATABASE_URL: str = "sqlite:///./sonic_autotrader.db"
    LOG_LEVEL: str = "INFO"

    @property
    def has_wallet_seed(self) -> bool:
        return bool(self.XRPL_WALLET_SEED and self.XRPL_WALLET_SEED.get_secret_value())
