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
    XRPL_INGESTION_ENABLED: bool = False
    XRPL_INGESTION_MODE: str = "disabled"
    XRPL_SHADOW_SOURCE: str = "static"
    XRPL_SNAPSHOT_THROTTLE_MS: int = Field(default=500, ge=0)
    XRPL_MAX_LEDGER_GAP: int = Field(default=128, ge=1)
    XRPL_DEFAULT_SHADOW_SIZE: float = Field(default=100.0, gt=0)
    XRPL_MAX_SNAPSHOT_AGE_MS: int = Field(default=15000, ge=1)
    XRPL_WALLET_SEED: SecretStr | None = Field(default=None, repr=False)

    MAX_TRADE_XRP: float = Field(default=5.0, gt=0)
    MAX_OPEN_POSITIONS: int = Field(default=3, ge=1)
    MAX_TOTAL_EXPOSURE_XRP: float = Field(default=20.0, gt=0)
    MAX_DAILY_LOSS_XRP: float = Field(default=10.0, gt=0)
    MIN_LIQUIDITY_XRP: float = Field(default=1000.0, ge=0)
    MAX_SPREAD_PCT: float = Field(default=8.0, ge=0)
    MAX_SLIPPAGE_PCT: float = Field(default=5.0, ge=0)

    ALPHA_DEPTH_LEVELS: int = Field(default=8, ge=2)
    ALPHA_STABILITY_WINDOW: int = Field(default=6, ge=3)
    ALPHA_MIN_SCORE: float = Field(default=0.72, ge=0, le=1)
    ALPHA_MIN_FILL_PROBABILITY: float = Field(default=0.85, ge=0, le=1)
    ALPHA_MAX_IMBALANCE_FLIP_RATE: float = Field(default=0.5, ge=0, le=1)
    ALPHA_COOLDOWN_FAILURES: int = Field(default=3, ge=1)
    ALPHA_COOLDOWN_MINUTES: int = Field(default=5, ge=1)

    DEFAULT_STOPLOSS_PCT: float = Field(default=10.0, ge=0)
    DEFAULT_TAKE_PROFIT_PCT: float = Field(default=20.0, ge=0)

    PAPER_STARTING_BALANCE_XRP: float = Field(default=1000.0, ge=0)
    STARTING_PAPER_BALANCE_XRP: float = Field(default=1000.0, ge=0)
    MAX_POSITION_XRP: float = Field(default=5.0, gt=0)
    MAX_TOTAL_LOCKED_XRP: float = Field(default=20.0, gt=0)
    MAX_CONCURRENT_POSITIONS: int = Field(default=3, ge=1)

    PERF_MONITOR_MINUTES: int = Field(default=15, ge=1)
    PERF_MAX_ACTUAL_SLIPPAGE_PCT: float = Field(default=8.0, ge=0)
    PERF_BOOK_COLLAPSE_RATIO: float = Field(default=0.35, ge=0, le=1)
    PERF_MIN_POST_ENTRY_LIQUIDITY_XRP: float = Field(default=150.0, ge=0)
    PERF_LIQUIDITY_DISAPPEAR_SECONDS: int = Field(default=30, ge=1)

    MAX_SNAPSHOT_AGE_MS: int = Field(default=1500, ge=1)
    EXECUTION_LATENCY_MS: int = Field(default=120, ge=0)
    SNAPSHOT_TO_DECISION_MS: int = Field(default=40, ge=0)
    DECISION_TO_SUBMISSION_MS: int = Field(default=30, ge=0)
    SUBMISSION_TO_INCLUSION_MS: int = Field(default=50, ge=0)
    XRPL_LEDGER_CLOSE_MS: int = Field(default=4000, ge=1000)
    MIN_LEDGER_DELAY: int = Field(default=1, ge=0)
    MAX_LEDGER_DELAY: int = Field(default=3, ge=1)
    EXECUTION_LIQUIDITY_HAIRCUT_PCT: float = Field(default=0.15, ge=0, le=0.95)
    EXECUTION_QUEUE_HAIRCUT_PCT: float = Field(default=0.15, ge=0, le=0.95)
    EXECUTION_LATENCY_HAIRCUT_PCT: float = Field(default=0.08, ge=0, le=0.95)
    EXECUTION_CONTENTION_HAIRCUT_PCT: float = Field(default=0.10, ge=0, le=0.95)
    EXECUTION_TRUSTLINE_DISCOUNT_PCT: float = Field(default=0.12, ge=0, le=0.95)
    EXECUTION_LEDGER_DRIFT_PCT: float = Field(default=0.10, ge=0, le=0.95)
    EXECUTION_WINDOW_SNAPSHOTS: int = Field(default=3, ge=0, le=20)
    EXECUTION_MIN_LEVEL_XRP: float = Field(default=0.1, ge=0)
    EXECUTION_MAX_LEVELS: int = Field(default=8, ge=1)
    MIN_EXIT_RETRY_MS: int = Field(default=5000, ge=0)
    MAX_EXIT_RETRIES: int = Field(default=5, ge=1)

    DATABASE_URL: str = "sqlite:///./sonic_autotrader.db"
    LOG_LEVEL: str = "INFO"

    @property
    def has_wallet_seed(self) -> bool:
        return bool(self.XRPL_WALLET_SEED and self.XRPL_WALLET_SEED.get_secret_value())
