from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.execution.execution_guard import ExecutionGuard, assert_core_execution_disabled
from app.main import create_app
from app.xrpl_core.transactions import submit_transaction


def test_execution_guard_default_fail_closed() -> None:
    result = assert_core_execution_disabled(Settings())

    assert result.allowed is False
    assert result.reason == "EXECUTION_DISABLED"
    assert result.to_dict()["is_executable"] is False
    assert result.to_dict()["requires_manual_approval"] is True


def test_execution_guard_blocks_forbidden_surfaces_even_if_flags_enabled() -> None:
    settings = Settings(EXECUTION_ENABLED=True, LIVE_TRADING_ENABLED=True)
    guard = ExecutionGuard(settings)

    for operation in ("xrpl.wallet", "xrpl.transaction", "submit", "autofill", "sign", "OfferCreate", "Payment"):
        result = guard.evaluate(operation=operation)
        assert result.allowed is False
        assert result.reason == "BLOCKED_XRPL_EXECUTION_SURFACE"


def test_submit_transaction_still_raises_fail_closed() -> None:
    settings = Settings(EXECUTION_ENABLED=True, LIVE_TRADING_ENABLED=True)

    with pytest.raises(NotImplementedError) as exc_info:
        submit_transaction(settings, {"TransactionType": "OfferCreate"})
    assert str(exc_info.value) == "BLOCKED_XRPL_EXECUTION_SURFACE"


@pytest.mark.parametrize(
    ("operation", "payload"),
    [
        ("submit_transaction", {"TransactionType": "OfferCreate"}),
        ("sign_transaction", {"note": "sign"}),
        ("autofill_transaction", {"note": "autofill"}),
        ("wallet_init", {"module": "xrpl.wallet"}),
    ],
)
def test_execution_guard_evaluate_blocks_submit_sign_autofill_wallet(
    operation: str,
    payload: dict[str, object],
) -> None:
    settings = Settings(EXECUTION_ENABLED=True, LIVE_TRADING_ENABLED=True)
    guard = ExecutionGuard(settings)

    result = guard.evaluate(operation=operation, payload=payload)

    assert result.allowed is False
    assert result.reason == "BLOCKED_XRPL_EXECUTION_SURFACE"
    assert result.is_executable is False
    assert result.requires_manual_approval is True


def test_execution_guard_api_is_read_only_and_non_executable() -> None:
    client = TestClient(create_app())

    first = client.get("/validation/execution-guard").json()
    second = client.get("/validation/execution-guard").json()

    assert first == second
    assert first["allowed"] is False
    assert first["is_shadow"] is True
    assert first["is_advisory"] is True
    assert first["is_executable"] is False
