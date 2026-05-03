"""Provider health checking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
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


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"
    FIXTURE_MISSING = "fixture_missing"
    STALE_FIXTURE = "stale_fixture"


@dataclass
class FixtureHealthReport:
    status: HealthStatus
    manifest_ok: bool
    dirs_ok: dict[str, bool]
    checksum_ok: bool
    ledger_range_ok: bool
    secret_scan_ok: bool
    issues: list[str]


def check_fixture_health(fixture_dir: Path) -> FixtureHealthReport:
    from sonic_xrpl.providers.fixture_store import FixtureStore, REQUIRED_DIRS

    if not fixture_dir.exists():
        return FixtureHealthReport(
            status=HealthStatus.FIXTURE_MISSING,
            manifest_ok=False,
            dirs_ok={d: False for d in REQUIRED_DIRS},
            checksum_ok=False,
            ledger_range_ok=False,
            secret_scan_ok=True,
            issues=[f"Fixture directory not found: {fixture_dir}"],
        )

    store = FixtureStore(fixture_dir)
    health = store.validate_health()

    manifest_ok = health["manifest_ok"]
    dirs_ok = health["dirs_ok"]
    secret_scan_ok = health["secret_scan_ok"]
    issues = health["issues"]

    checksum_ok = manifest_ok
    ledger_range_ok = manifest_ok

    if not manifest_ok:
        status = HealthStatus.FIXTURE_MISSING
    elif not all(dirs_ok.values()):
        status = HealthStatus.DEGRADED
    elif not secret_scan_ok:
        status = HealthStatus.DEGRADED
    else:
        status = HealthStatus.HEALTHY

    return FixtureHealthReport(
        status=status,
        manifest_ok=manifest_ok,
        dirs_ok=dirs_ok,
        checksum_ok=checksum_ok,
        ledger_range_ok=ledger_range_ok,
        secret_scan_ok=secret_scan_ok,
        issues=issues,
    )
