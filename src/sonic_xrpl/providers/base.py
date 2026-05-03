"""Abstract provider contracts for XRPL V2.

Architecture Rules:
- Providers must be replaceable (Rule #2)
- Clio is historical/read only (Rule #3)
- Submission is BLOCKED via live_guard (Rule #4)

Provider types:
- LedgerProvider: current ledger state (rippled, public RPC)
- HistoricalProvider: historical validated data (Clio)
- SubmissionProvider: transaction submission (BLOCKED in Phase 45)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class ProviderType(str, Enum):
    """Known provider backend types."""

    RIPPLED = "rippled"
    CLIO = "clio"
    PUBLIC_RPC = "public_rpc"
    MOCK = "mock"
    XAHAU_RESEARCH = "xahau_research"


class LedgerProvider(ABC):
    """Abstract interface for reading current XRPL ledger state."""

    provider_type: ProviderType = ProviderType.MOCK

    @abstractmethod
    def get_server_info(self) -> dict[str, Any]:
        """Return server_info response."""

    @abstractmethod
    def get_latest_validated_ledger(self) -> dict[str, Any]:
        """Return the latest validated ledger summary."""

    @abstractmethod
    def get_account_info(self, account: str) -> dict[str, Any]:
        """Return account_info for the given account address."""

    @abstractmethod
    def get_account_tx(
        self,
        account: str,
        ledger_min: int | None = None,
        ledger_max: int | None = None,
    ) -> dict[str, Any]:
        """Return account_tx for the given account."""

    @abstractmethod
    def get_ledger_entry(self, **kwargs: Any) -> dict[str, Any]:
        """Return a ledger entry by type/index."""

    @abstractmethod
    def get_orderbook(self, **kwargs: Any) -> dict[str, Any]:
        """Return order book offers."""

    @abstractmethod
    def get_amm_info(self, **kwargs: Any) -> dict[str, Any]:
        """Return AMM pool info."""

    @abstractmethod
    def get_mpt_holders(self, **kwargs: Any) -> dict[str, Any]:
        """Return MPT holders for an issuance."""

    @abstractmethod
    def close(self) -> None:
        """Release provider resources."""


class HistoricalProvider(ABC):
    """Abstract interface for reading historical XRPL data (Clio-style).

    NOTE: Clio is read/historical only. Do NOT use for transaction submission.
    """

    provider_type: ProviderType = ProviderType.CLIO

    @abstractmethod
    def get_validated_transactions(self, **kwargs: Any) -> dict[str, Any]:
        """Return validated transactions matching the given filters."""

    @abstractmethod
    def get_account_history(self, **kwargs: Any) -> dict[str, Any]:
        """Return paginated transaction history for an account."""

    @abstractmethod
    def get_ledger_range(self) -> dict[str, Any]:
        """Return the range of ledgers available in this provider."""


class SubmissionProvider(ABC):
    """Abstract interface for transaction submission.

    BLOCKED in Phase 45 — real submission raises LiveTradingDisabledError.
    This interface exists only as a contract; all implementations must
    check live_guard before any network call.
    """

    provider_type: ProviderType = ProviderType.MOCK

    @abstractmethod
    def submit(self, **kwargs: Any) -> dict[str, Any]:
        """Submit a signed transaction blob. BLOCKED in Phase 45."""

    @abstractmethod
    def submit_and_wait(self, **kwargs: Any) -> dict[str, Any]:
        """Submit and wait for validation. BLOCKED in Phase 45."""
