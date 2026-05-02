"""Fixture-backed ledger provider — loads data from JSON fixture files.

Useful for deterministic replay testing without network access.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sonic_xrpl.providers.base import LedgerProvider, ProviderType
from sonic_xrpl.providers.mocks import MockLedgerProvider


class FixtureLedgerProvider(LedgerProvider):
    """A LedgerProvider backed by JSON fixture files.

    Falls back to MockLedgerProvider data if fixture not found.
    """

    provider_type = ProviderType.MOCK

    def __init__(self, fixture_dir: Path | None = None) -> None:
        self._fixture_dir = fixture_dir or Path("tests/fixtures")
        self._fallback = MockLedgerProvider()

    def _load(self, name: str) -> dict[str, Any] | None:
        """Load a fixture by name. Returns None if not found."""
        path = self._fixture_dir / f"{name}.json"
        if path.exists():
            with path.open() as f:
                return json.load(f)
        return None

    def get_server_info(self) -> dict[str, Any]:
        return self._load("server_info") or self._fallback.get_server_info()

    def get_latest_validated_ledger(self) -> dict[str, Any]:
        return (
            self._load("latest_validated_ledger")
            or self._fallback.get_latest_validated_ledger()
        )

    def get_account_info(self, account: str) -> dict[str, Any]:
        return (
            self._load(f"account_info_{account}")
            or self._fallback.get_account_info(account)
        )

    def get_account_tx(
        self,
        account: str,
        ledger_min: int | None = None,
        ledger_max: int | None = None,
    ) -> dict[str, Any]:
        return (
            self._load(f"account_tx_{account}")
            or self._fallback.get_account_tx(account, ledger_min, ledger_max)
        )

    def get_ledger_entry(self, **kwargs: Any) -> dict[str, Any]:
        return self._fallback.get_ledger_entry(**kwargs)

    def get_orderbook(self, **kwargs: Any) -> dict[str, Any]:
        return self._load("orderbook") or self._fallback.get_orderbook(**kwargs)

    def get_amm_info(self, **kwargs: Any) -> dict[str, Any]:
        return self._load("amm_info") or self._fallback.get_amm_info(**kwargs)

    def get_mpt_holders(self, **kwargs: Any) -> dict[str, Any]:
        return self._fallback.get_mpt_holders(**kwargs)

    def close(self) -> None:
        pass
