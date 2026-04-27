"""XRPL JSON-RPC client wrapper."""

from __future__ import annotations

from xrpl.clients import JsonRpcClient

from app.config import settings
from app.telemetry import get_logger

logger = get_logger("xrpl_core.client")

_client: JsonRpcClient | None = None


def get_client() -> JsonRpcClient:
    """Return a module-level singleton XRPL JSON-RPC client."""
    global _client
    if _client is None:
        logger.info("Initialising XRPL JSON-RPC client", url=settings.xrpl_rpc_url)
        _client = JsonRpcClient(settings.xrpl_rpc_url)
    return _client


def close_client() -> None:
    """Explicitly close / reset the client (useful in tests)."""
    global _client
    _client = None
