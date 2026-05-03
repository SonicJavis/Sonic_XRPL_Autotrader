"""Failover provider — wraps multiple LedgerProviders with automatic fallback."""

from __future__ import annotations

from typing import Any

from sonic_xrpl.core.errors import ProviderError
from sonic_xrpl.providers.base import LedgerProvider, ProviderType


class FailoverProvider(LedgerProvider):
    """Tries each provider in order, falling back on error.

    Useful for resilient read operations during development.
    Does NOT support submission (blocked by live_guard).
    """

    provider_type = ProviderType.MOCK

    def __init__(self, providers: list[LedgerProvider]) -> None:
        if not providers:
            raise ValueError("FailoverProvider requires at least one provider")
        self._providers = providers
        self._failover_reasons: list[str] = []

    @property
    def last_failover_reasons(self) -> list[str]:
        return list(self._failover_reasons)

    def _call(self, method: str, **kwargs: Any) -> dict[str, Any]:
        """Try each provider in order, returning the first success."""
        self._failover_reasons = []
        last_error: Exception | None = None
        for provider in self._providers:
            try:
                return getattr(provider, method)(**kwargs)
            except Exception as exc:
                self._failover_reasons.append(f"{type(provider).__name__}: {exc}")
                last_error = exc
        raise ProviderError(
            f"All providers failed for {method!r}: {last_error}"
        )

    def get_server_info(self) -> dict[str, Any]:
        return self._call("get_server_info")

    def get_latest_validated_ledger(self) -> dict[str, Any]:
        return self._call("get_latest_validated_ledger")

    def get_account_info(self, account: str) -> dict[str, Any]:
        return self._call("get_account_info", account=account)

    def get_account_lines(self, account: str) -> dict[str, Any]:
        return self._call("get_account_lines", account=account)

    def get_account_tx(
        self,
        account: str,
        ledger_min: int | None = None,
        ledger_max: int | None = None,
    ) -> dict[str, Any]:
        return self._call(
            "get_account_tx",
            account=account,
            ledger_min=ledger_min,
            ledger_max=ledger_max,
        )

    def get_ledger_entry(self, **kwargs: Any) -> dict[str, Any]:
        return self._call("get_ledger_entry", **kwargs)

    def get_orderbook(self, **kwargs: Any) -> dict[str, Any]:
        return self._call("get_orderbook", **kwargs)

    def get_amm_info(self, **kwargs: Any) -> dict[str, Any]:
        return self._call("get_amm_info", **kwargs)

    def get_mpt_holders(self, **kwargs: Any) -> dict[str, Any]:
        return self._call("get_mpt_holders", **kwargs)

    def close(self) -> None:
        for provider in self._providers:
            try:
                provider.close()
            except Exception:
                pass
