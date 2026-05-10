"""Hot wallet architecture policy (read-only for Week 1).

No signing and no submission are performed here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal


MAX_HOT_WALLET_XRP = Decimal("10000")


@dataclass(frozen=True)
class HotWalletStatus:
    seed_configured: bool
    spend_limit_xrp: Decimal
    account: str
    balance_xrp: Decimal
    sequence: int | None
    within_limit: bool
    blocked_reason: str | None


class HotWalletPolicy:
    """Enforces spending ceiling and read-only state inspection."""

    def __init__(
        self,
        *,
        seed_env_key: str = "SONIC_HOT_WALLET_SEED",
        account_env_key: str = "SONIC_HOT_WALLET_ACCOUNT",
        max_xrp: Decimal = MAX_HOT_WALLET_XRP,
    ) -> None:
        self.seed_env_key = seed_env_key
        self.account_env_key = account_env_key
        self.max_xrp = max_xrp

    def configured_account(self) -> str:
        return os.environ.get(self.account_env_key, "").strip()

    def seed_configured(self) -> bool:
        seed = os.environ.get(self.seed_env_key, "").strip()
        return bool(seed)

    def evaluate(self, *, balance_xrp: Decimal, sequence: int | None) -> HotWalletStatus:
        account = self.configured_account()
        within_limit = balance_xrp <= self.max_xrp
        blocked_reason = None if within_limit else "hot_wallet_limit_exceeded"
        return HotWalletStatus(
            seed_configured=self.seed_configured(),
            spend_limit_xrp=self.max_xrp,
            account=account,
            balance_xrp=balance_xrp,
            sequence=sequence,
            within_limit=within_limit,
            blocked_reason=blocked_reason,
        )

    def from_account_info(self, account_info: dict[str, object]) -> HotWalletStatus:
        result = account_info.get("account_data") if isinstance(account_info, dict) else {}
        if not isinstance(result, dict):
            result = {}
        balance_drops = str(result.get("Balance", "0"))
        sequence_raw = result.get("Sequence")
        balance_xrp = (Decimal(balance_drops) / Decimal("1000000")).quantize(Decimal("0.000001"))
        sequence = int(sequence_raw) if sequence_raw is not None else None
        return self.evaluate(balance_xrp=balance_xrp, sequence=sequence)
