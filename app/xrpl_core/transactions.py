"""XRPL transaction builders and safe submit helpers.

Real submission is gated behind LIVE_TRADING_ENABLED.
"""

from __future__ import annotations

from decimal import Decimal

from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import OfferCreate
from xrpl.transaction import submit_and_wait
from xrpl.wallet import Wallet

from app.config import settings
from app.telemetry import get_logger, new_request_id
from app.xrpl_core.client import get_client

logger = get_logger("xrpl_core.transactions")


def build_offer_create(
    wallet: Wallet,
    taker_pays_xrp: float,
    taker_gets_currency: str,
    taker_gets_issuer: str,
    taker_gets_value: str,
) -> OfferCreate:
    """Build an OfferCreate transaction (does NOT submit).

    Args:
        wallet: The signing wallet.
        taker_pays_xrp: Amount of XRP (in XRP, not drops) the taker pays.
        taker_gets_currency: Currency code the taker receives.
        taker_gets_issuer: Issuer of the currency the taker receives.
        taker_gets_value: String amount of the issued currency the taker receives.

    Returns:
        An unsigned OfferCreate transaction object.
    """
    drops = str(int(Decimal(str(taker_pays_xrp)) * 1_000_000))
    offer = OfferCreate(
        account=wallet.address,
        taker_pays=drops,
        taker_gets=IssuedCurrencyAmount(
            currency=taker_gets_currency,
            issuer=taker_gets_issuer,
            value=taker_gets_value,
        ),
    )
    logger.debug(
        "Built OfferCreate",
        account=wallet.address,
        taker_pays_xrp=taker_pays_xrp,
        taker_gets_currency=taker_gets_currency,
    )
    return offer


def safe_submit(wallet: Wallet, transaction: OfferCreate) -> dict:
    """Submit a transaction to the XRPL — only if live trading is enabled.

    Args:
        wallet: The signing wallet.
        transaction: The transaction to submit.

    Returns:
        The response dict from xrpl-py.

    Raises:
        RuntimeError: If live trading is not enabled.
    """
    request_id = new_request_id()

    if not settings.is_live_trading:
        logger.warning(
            "Live trading is DISABLED — transaction NOT submitted",
            request_id=request_id,
            account=wallet.address,
        )
        raise RuntimeError(
            "LIVE_TRADING_ENABLED is false. Transaction blocked for safety."
        )

    logger.info(
        "Submitting transaction to XRPL",
        request_id=request_id,
        account=wallet.address,
        tx_type=type(transaction).__name__,
    )
    client = get_client()
    response = submit_and_wait(transaction, client, wallet)
    logger.info(
        "Transaction submitted",
        request_id=request_id,
        result=response.result.get("meta", {}).get("TransactionResult"),
    )
    return response.result
