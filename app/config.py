from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    xrpl_network_url: str = Field(default="https://s.altnet.rippletest.net:51234")
    wallet_seed: str = Field(default="")
    trading_symbol: str = Field(default="XRP/USD")
    trade_amount: float = Field(default=5.0, gt=0)
    polling_interval_seconds: int = Field(default=5, ge=1)
    log_level: str = Field(default="INFO")
