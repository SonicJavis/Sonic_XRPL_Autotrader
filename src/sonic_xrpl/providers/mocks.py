"""Mock providers for offline testing.

All mock data is deterministic and requires no network access.
MockSubmissionProvider ALWAYS raises LiveTradingDisabledError.
"""

from __future__ import annotations

from typing import Any

from sonic_xrpl.core.errors import LiveTradingDisabledError
from sonic_xrpl.providers.base import (
    HistoricalProvider,
    LedgerProvider,
    ProviderType,
    SubmissionProvider,
)


class MockLedgerProvider(LedgerProvider):
    """Deterministic mock implementation of LedgerProvider for offline testing."""

    provider_type = ProviderType.MOCK

    def get_server_info(self) -> dict[str, Any]:
        return {
            "info": {
                "build_version": "1.12.0-mock",
                "complete_ledgers": "32570-90000000",
                "validated_ledger": {
                    "hash": "ABCDEF1234567890",
                    "ledger_index": 90_000_000,
                    "close_time": 0,
                },
                "server_state": "full",
            },
            "status": "success",
        }

    def get_latest_validated_ledger(self) -> dict[str, Any]:
        return {
            "ledger_index": 90_000_000,
            "ledger_hash": "ABCDEF1234567890",
            "close_time_iso": "2026-01-01T00:00:00Z",
            "validated": True,
        }

    def get_account_info(self, account: str) -> dict[str, Any]:
        return {
            "account_data": {
                "Account": account,
                "Balance": "100000000",
                "Flags": 0,
                "Sequence": 1,
            },
            "validated": True,
        }

    def get_account_tx(
        self,
        account: str,
        ledger_min: int | None = None,
        ledger_max: int | None = None,
    ) -> dict[str, Any]:
        return {"account": account, "transactions": [], "validated": True}

    def get_ledger_entry(self, **kwargs: Any) -> dict[str, Any]:
        return {"node": {}, "validated": True}

    def get_orderbook(self, **kwargs: Any) -> dict[str, Any]:
        return {"offers": [], "validated": True}

    def get_amm_info(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "amm": {
                "amount": "1000000000",
                "amount2": {"currency": "USD", "issuer": "rMockIssuer", "value": "1000"},
                "lp_token": {"currency": "039C99CD9AB0B9C62", "issuer": "rMockAMM", "value": "100"},
                "trading_fee": 500,
            },
            "validated": True,
        }

    def get_mpt_holders(self, **kwargs: Any) -> dict[str, Any]:
        return {"mpt_issuance_id": kwargs.get("mpt_issuance_id", ""), "holders": []}

    def close(self) -> None:
        pass


class MockHistoricalProvider(HistoricalProvider):
    """Deterministic mock implementation of HistoricalProvider."""

    provider_type = ProviderType.CLIO

    def get_validated_transactions(self, **kwargs: Any) -> dict[str, Any]:
        return {"transactions": [], "validated": True}

    def get_account_history(self, **kwargs: Any) -> dict[str, Any]:
        return {"transactions": [], "marker": None}

    def get_ledger_range(self) -> dict[str, Any]:
        return {"ledger_min": 32570, "ledger_max": 90_000_000}


class MockSubmissionProvider(SubmissionProvider):
    """Mock SubmissionProvider — ALWAYS raises LiveTradingDisabledError.

    Exists only to satisfy the SubmissionProvider interface contract.
    Real submission is unconditionally blocked in Phase 45.
    """

    provider_type = ProviderType.MOCK

    def submit(self, **kwargs: Any) -> dict[str, Any]:
        raise LiveTradingDisabledError(
            "MockSubmissionProvider.submit() called — live trading is BLOCKED in Phase 45. "
            "This provider exists only as a contract placeholder."
        )

    def submit_and_wait(self, **kwargs: Any) -> dict[str, Any]:
        raise LiveTradingDisabledError(
            "MockSubmissionProvider.submit_and_wait() called — live trading is BLOCKED in Phase 45. "
            "This provider exists only as a contract placeholder."
        )
