"""XRPL wallet helpers.

WARNING: The wallet seed is read from environment only.
It is NEVER logged or persisted to disk.
"""

from __future__ import annotations

from xrpl.wallet import Wallet

from app.config import settings
from app.telemetry import get_logger

logger = get_logger("xrpl_core.wallet")


def load_wallet() -> Wallet:
    """Load the trading wallet from the environment seed.

    Raises:
        RuntimeError: If the seed is not configured or live trading is disabled.
    """
    if not settings.is_live_trading:
        raise RuntimeError(
            "load_wallet() called but LIVE_TRADING_ENABLED is false. "
            "Wallet is only available in live-trading mode."
        )

    seed = settings.xrpl_wallet_seed
    if not seed:
        raise RuntimeError(
            "XRPL_WALLET_SEED is not set in environment. "
            "Configure it before enabling live trading."
        )

    wallet = Wallet.from_seed(seed)
    # Log address but NEVER log the seed.
    logger.info("Wallet loaded", address=wallet.address)
    return wallet
