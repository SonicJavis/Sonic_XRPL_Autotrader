from __future__ import annotations

from decimal import Decimal

import pytest

from sonic_xrpl.wallet.hot_wallet import HotWalletPolicy


def test_hot_wallet_blocks_when_balance_exceeds_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONIC_HOT_WALLET_ACCOUNT", "rHotWallet")
    monkeypatch.setenv("SONIC_HOT_WALLET_SEED", "sTestSeed")
    policy = HotWalletPolicy()
    status = policy.evaluate(balance_xrp=Decimal("10000.000001"), sequence=12)
    assert status.within_limit is False
    assert status.blocked_reason == "hot_wallet_limit_exceeded"


def test_hot_wallet_allows_when_within_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONIC_HOT_WALLET_ACCOUNT", "rHotWallet")
    monkeypatch.setenv("SONIC_HOT_WALLET_SEED", "sTestSeed")
    policy = HotWalletPolicy()
    status = policy.evaluate(balance_xrp=Decimal("9999.5"), sequence=77)
    assert status.within_limit is True
    assert status.blocked_reason is None
    assert status.account == "rHotWallet"
    assert status.seed_configured is True


def test_hot_wallet_parses_account_info_fixture_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SONIC_HOT_WALLET_ACCOUNT", "rHotWallet")
    policy = HotWalletPolicy()
    status = policy.from_account_info(
        {
            "account_data": {
                "Balance": "5000000000",
                "Sequence": 42,
            }
        }
    )
    assert status.balance_xrp == Decimal("5000.000000")
    assert status.sequence == 42
