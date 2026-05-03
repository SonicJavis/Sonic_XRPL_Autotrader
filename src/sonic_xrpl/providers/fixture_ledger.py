"""Fixture-backed LedgerProvider using FixtureStore.

Raises FixtureMissingError when fixture not found — no fallback to mock.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sonic_xrpl.providers.base import LedgerProvider, ProviderType
from sonic_xrpl.providers.fixture_store import FixtureStore


class FixtureLedgerProvider(LedgerProvider):
    """A LedgerProvider backed by structured JSON fixture files via FixtureStore."""

    provider_type = ProviderType.FIXTURE

    def __init__(self, fixture_dir: Path) -> None:
        self._store = FixtureStore(fixture_dir)

    def get_server_info(self) -> dict[str, Any]:
        return self._store.load_server_info()

    def get_latest_validated_ledger(self) -> dict[str, Any]:
        return self._store.load_latest_ledger()

    def get_account_info(self, account: str) -> dict[str, Any]:
        return self._store.load_account_info(account)

    def get_account_lines(self, account: str) -> dict[str, Any]:
        return self._store.load_account_lines(account)

    def get_account_tx(
        self,
        account: str,
        ledger_min: int | None = None,
        ledger_max: int | None = None,
    ) -> dict[str, Any]:
        return self._store.load_account_tx(account, ledger_min=ledger_min, ledger_max=ledger_max)

    def get_ledger_entry(self, **kwargs: Any) -> dict[str, Any]:
        ledger_index = kwargs.get("ledger_index")
        if ledger_index is not None:
            return self._store.load_ledger(int(ledger_index))
        return self._store.load_latest_ledger()

    def get_orderbook(self, **kwargs: Any) -> dict[str, Any]:
        asset_a = str(kwargs.get("taker_gets", "XRP"))
        asset_b = str(kwargs.get("taker_pays", "USD"))
        return self._store.load_orderbook(asset_a, asset_b)

    def get_amm_info(self, **kwargs: Any) -> dict[str, Any]:
        asset_a = str(kwargs.get("asset", kwargs.get("asset_a", "XRP")))
        asset_b = str(kwargs.get("asset2", kwargs.get("asset_b", "USD")))
        return self._store.load_amm_info(asset_a, asset_b)

    def get_mpt_holders(self, **kwargs: Any) -> dict[str, Any]:
        mpt_issuance_id = str(kwargs.get("mpt_issuance_id", ""))
        return self._store.load_mpt_holders(mpt_issuance_id)

    def close(self) -> None:
        pass
