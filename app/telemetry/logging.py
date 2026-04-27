from __future__ import annotations

import json
import logging


def get_logger(name: str = "sonic.autotrader") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def log_event(logger: logging.Logger, payload: dict[str, object]) -> None:
    safe_payload = dict(payload)
    safe_payload.pop("XRPL_WALLET_SEED", None)
    safe_payload.pop("private_key", None)
    logger.info(json.dumps(safe_payload, default=str))
