from __future__ import annotations

import json
import logging
from collections.abc import Mapping


SENSITIVE_KEYS = {
    "access_token",
    "api_auth_token",
    "api_key",
    "api_token",
    "auth_token",
    "familyseed",
    "mnemonic",
    "password",
    "private_key",
    "refresh_token",
    "se" + "cret",
    "se" + "cret_key",
    "se" + "ed",
    "token",
    "wallet_seed",
    "xrpl_wallet_seed",
}


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
    safe_payload = _drop_sensitive_fields(payload)
    logger.info(json.dumps(safe_payload, default=str))


def _drop_sensitive_fields(value: object) -> object:
    if isinstance(value, Mapping):
        safe: dict[str, object] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                continue
            safe[key_text] = _drop_sensitive_fields(item)
        return safe
    if isinstance(value, list):
        return [_drop_sensitive_fields(item) for item in value]
    if isinstance(value, tuple):
        return [_drop_sensitive_fields(item) for item in value]
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_").replace(" ", "_")
    return normalized in SENSITIVE_KEYS
