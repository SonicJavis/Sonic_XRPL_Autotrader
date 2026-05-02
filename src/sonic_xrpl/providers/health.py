"""Provider health checking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sonic_xrpl.providers.base import LedgerProvider, ProviderType


@dataclass
class ProviderHealth:
    """Health report for a single provider."""

    provider_type: "ProviderType"
    is_alive: bool
    latency_ms: float | None = None
    last_checked: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    error_message: str | None = None


def check_provider_health(provider: "LedgerProvider") -> ProviderHealth:
    """Attempt a lightweight health check on the provider.

    For mock providers this always returns healthy.
    For real providers, tries get_server_info().
    """
    from sonic_xrpl.providers.base import ProviderType

    import time

    start = time.monotonic()
    try:
        provider.get_server_info()
        latency_ms = (time.monotonic() - start) * 1000
        return ProviderHealth(
            provider_type=provider.provider_type,
            is_alive=True,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as exc:
        return ProviderHealth(
            provider_type=provider.provider_type,
            is_alive=False,
            error_message=str(exc),
        )
