import logging

from app.config import Settings
from app.telemetry.logging import log_event
from app.xrpl_core.transactions import submit_transaction


def test_no_transaction_submission_possible() -> None:
    settings = Settings(LIVE_TRADING_ENABLED=False)
    try:
        submit_transaction(settings, {"tx": "blob"})
        assert False, "submit_transaction should raise when live trading disabled"
    except NotImplementedError:
        assert True


def test_secrets_not_logged() -> None:
    logger = logging.getLogger("test.safety")
    logger.handlers = []
    records: list[str] = []

    class _Handler(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    logger.addHandler(_Handler())
    logger.setLevel(logging.INFO)

    log_event(logger, {"event": "x", "XRPL_WALLET_SEED": "sSUPERSECRET", "private_key": "abc", "ok": 1})

    assert records
    payload = records[-1]
    assert "sSUPERSECRET" not in payload
    assert "private_key" not in payload
