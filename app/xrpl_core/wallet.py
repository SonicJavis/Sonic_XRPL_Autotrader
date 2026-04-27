from __future__ import annotations

from app.config import Settings


class WalletInfo:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def seed_present(self) -> bool:
        return self._settings.has_wallet_seed

    def masked_seed(self) -> str:
        if not self._settings.has_wallet_seed:
            return "<not-configured>"
        return "***REDACTED***"
