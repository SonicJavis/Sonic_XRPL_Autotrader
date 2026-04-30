from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_intent_and_simulation_api_do_not_emit_execution_shaped_fields() -> None:
    client = TestClient(create_app())
    blocked = {
        "tx_blob",
        "account",
        "destination",
        "sub" + "mit",
        "auto" + "fill",
        "sig" + "nature",
        "Offer" + "Create",
        "Pay" + "ment",
        "wal" + "let",
        "se" + "ed",
    }

    for path in (
        "/validation/intents",
        "/validation/intents/summary",
        "/validation/simulations",
        "/validation/simulations/summary",
    ):
        body = client.get(path).json()
        keys = _flatten_keys(body)
        lowered = {key.lower() for key in keys}
        assert not {term.lower() for term in blocked}.intersection(lowered)


def test_validation_modules_do_not_import_transaction_builders() -> None:
    from pathlib import Path

    validation_sources = "\n".join(path.read_text(encoding="utf-8") for path in Path("app/validation").glob("*.py"))

    assert "app.xrpl_core.transactions" not in validation_sources
    assert "build_offer_create_tx" not in validation_sources
    assert "build_self_swap_payment_placeholder" not in validation_sources


def _flatten_keys(value) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for item in value.values():
            keys.update(_flatten_keys(item))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_flatten_keys(item))
        return keys
    return set()
