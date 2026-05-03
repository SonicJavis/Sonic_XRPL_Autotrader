"""FixtureMarketDataProvider — offline market data from fixture store."""

from __future__ import annotations

from typing import Any

from sonic_xrpl.providers.fixture_store import FixtureStore


class FixtureMarketDataProvider:
    """Provides market data snapshots from offline fixture files."""

    def __init__(self, fixture_store: FixtureStore) -> None:
        self._store = fixture_store

    def get_orderbook_snapshot(self, asset_a: str, asset_b: str) -> dict[str, Any]:
        return self._store.load_orderbook(asset_a, asset_b)

    def get_amm_snapshot(self, asset_a: str, asset_b: str) -> dict[str, Any]:
        return self._store.load_amm_info(asset_a, asset_b)

    def get_price_series(
        self,
        asset_key: str,
        start_ledger: int | None = None,
        end_ledger: int | None = None,
    ) -> dict[str, Any]:
        """Derive price series from available fixtures. Returns empty with limitation if no data."""
        try:
            manifest = self._store.load_manifest()
            _ = manifest.ledger_min
        except Exception:
            return {
                "data": [],
                "limitation": f"no fixture data available for price series: {asset_key}",
            }
        return {
            "data": [],
            "limitation": (
                f"price series not available from fixture store for {asset_key}; "
                "fixtures contain only point-in-time snapshots"
            ),
        }

    def get_liquidity_series(
        self,
        asset_key: str,
        start_ledger: int | None = None,
        end_ledger: int | None = None,
    ) -> dict[str, Any]:
        """Derive liquidity series from available fixtures."""
        return {
            "data": [],
            "limitation": (
                f"liquidity series not available from fixture store for {asset_key}; "
                "fixtures contain only point-in-time snapshots"
            ),
        }
