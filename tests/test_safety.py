import logging

import pytest

from app.config import Settings
from app.telemetry.logging import log_event
from app.xrpl_core.transactions import submit_transaction


def test_no_transaction_submission_possible() -> None:
    settings = Settings(LIVE_TRADING_ENABLED=False)
    with pytest.raises(NotImplementedError):
        submit_transaction(settings, {"tx": "blob"})


def test_secrets_not_logged() -> None:
    logger = logging.getLogger("test.safety")
    logger.handlers = []
    records: list[str] = []

    class _Handler(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    logger.addHandler(_Handler())
    logger.setLevel(logging.INFO)

    log_event(
        logger,
        {
            "event": "x",
            "XRPL_WALLET_SEED": "sSUPERSECRET",
            "private_key": "abc",
            "seed": "sNESTED",
            "wallet_seed": "sWALLET",
            "secret_key": "hidden",
            "metadata": {"api_token": "tok_123", "ok": 1},
            "rows": [{"password": "pw", "value": 2}],
            "ok": 1,
        },
    )

    assert records
    payload = records[-1]
    for forbidden in ("sSUPERSECRET", "abc", "sNESTED", "sWALLET", "hidden", "tok_123", "pw"):
        assert forbidden not in payload
    for forbidden_key in ("XRPL_WALLET_SEED", "private_key", "wallet_seed", "secret_key", "api_token", "password"):
        assert forbidden_key not in payload
    assert '"ok": 1' in payload
