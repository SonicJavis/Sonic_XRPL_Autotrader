from __future__ import annotations

import pytest

from app.config import Settings
from app.xrpl_core.transactions import submit_transaction
from sonic_xrpl.core.errors import LiveTradingDisabledError
from sonic_xrpl.core.modes import RuntimeMode
from sonic_xrpl.execution.live_guard import (
    assert_can_submit,
    block_autofill,
    block_signing,
    block_wallet_construction,
)


@pytest.mark.parametrize("mode", list(RuntimeMode))
def test_unified_scaffold_assert_can_submit_is_fail_closed(mode: RuntimeMode) -> None:
    with pytest.raises(LiveTradingDisabledError):
        assert_can_submit(mode)


@pytest.mark.parametrize("blocker", [block_signing, block_autofill, block_wallet_construction])
def test_unified_scaffold_blockers_always_raise(blocker) -> None:
    with pytest.raises(LiveTradingDisabledError):
        blocker()


def test_unified_scaffold_app_submit_path_still_blocked() -> None:
    settings = Settings(EXECUTION_ENABLED=True, LIVE_TRADING_ENABLED=True)
    with pytest.raises(NotImplementedError) as exc_info:
        submit_transaction(settings, {"TransactionType": "OfferCreate"})
    assert str(exc_info.value) == "BLOCKED_XRPL_EXECUTION_SURFACE"
