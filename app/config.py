"""Application configuration — loaded from .env via Pydantic Settings."""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration for Sonic XRPL Autotrader."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Bot mode ────────────────────────────────────────────────────────────
    bot_mode: str = Field(default="PAPER_TRADING", description="BOT_MODE env var")
    live_trading_enabled: bool = Field(
        default=False,
        description="Master live-trading gate — must be explicitly set to true",
    )

    # ── XRPL network ────────────────────────────────────────────────────────
    xrpl_rpc_url: str = Field(default="https://s1.ripple.com:51234")
    xrpl_ws_url: str = Field(default="wss://s1.ripple.com")

    # ── Wallet ───────────────────────────────────────────────────────────────
    xrpl_wallet_seed: str | None = Field(
        default=None,
        description="XRPL wallet seed — required only for live trading",
    )

    # ── Risk limits ──────────────────────────────────────────────────────────
    max_trade_xrp: float = Field(default=5.0, gt=0)
    max_open_positions: int = Field(default=3, gt=0)

    # ── Paper trade defaults ─────────────────────────────────────────────────
    paper_stop_loss_pct: float = Field(default=0.10, gt=0, le=1)
    paper_take_profit_pct: float = Field(default=0.20, gt=0, le=1)

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(default="sqlite:///./sonic_trader.db")

    # ── API ──────────────────────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, gt=0, le=65535)

    @field_validator("bot_mode")
    @classmethod
    def _validate_bot_mode(cls, v: str) -> str:
        allowed = {"PAPER_TRADING", "LIVE_TRADING"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"bot_mode must be one of {allowed}, got {v!r}")
        return upper

    @property
    def is_paper_trading(self) -> bool:
        return self.bot_mode == "PAPER_TRADING" or not self.live_trading_enabled

    @property
    def is_live_trading(self) -> bool:
        return self.bot_mode == "LIVE_TRADING" and self.live_trading_enabled


# Module-level singleton — import `settings` everywhere.
settings = Settings()
