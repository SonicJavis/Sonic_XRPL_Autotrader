"""XRPL WebSocket ledger stream listener.

Connects to the XRPL public WebSocket feed, subscribes to
transactions, and logs them.  No trading logic is executed here.
"""

from __future__ import annotations

import asyncio
import json

import websockets

from app.config import settings
from app.telemetry import get_logger

logger = get_logger("xrpl_core.ledger_stream")

_SUBSCRIBE_MSG = json.dumps(
    {
        "id": 1,
        "command": "subscribe",
        "streams": ["transactions"],
    }
)


async def stream_transactions(stop_event: asyncio.Event | None = None) -> None:
    """Connect to the XRPL WebSocket and log incoming transactions.

    Args:
        stop_event: If provided, the stream will stop when the event is set.
    """
    url = settings.xrpl_ws_url
    logger.info("Connecting to XRPL WebSocket", url=url)

    async with websockets.connect(url) as ws:  # type: ignore[attr-defined]
        await ws.send(_SUBSCRIBE_MSG)
        logger.info("Subscribed to transactions stream")

        while True:
            if stop_event and stop_event.is_set():
                logger.info("Stop event received — closing ledger stream")
                break

            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
                msg = json.loads(raw)
                tx_type = msg.get("transaction", {}).get("TransactionType", "unknown")
                account = msg.get("transaction", {}).get("Account", "unknown")
                logger.debug(
                    "XRPL transaction received",
                    tx_type=tx_type,
                    account=account,
                )
            except asyncio.TimeoutError:
                continue
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed — attempting reconnect")
                break
