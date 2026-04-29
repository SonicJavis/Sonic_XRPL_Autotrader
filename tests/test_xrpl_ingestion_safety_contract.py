from pathlib import Path

from app.live.xrpl_readonly_ws_adapter import XRPLReadOnlyWebSocketAdapter, _validate_readonly_command


class FailingClient:
    def connect(self):
        return False


def test_adapter_source_does_not_construct_forbidden_commands() -> None:
    source = Path("app/live/xrpl_readonly_ws_adapter.py").read_text(encoding="utf-8")
    for term in ("submit", "sign", "wallet", "autofill", "OfferCreate", "Payment"):
        assert term not in source


def test_validator_rejects_forbidden_method_names() -> None:
    for term in ("submit", "sign", "wallet", "autofill", "OfferCreate", "Payment"):
        try:
            _validate_readonly_command({"command": term, "streams": ["ledger"]})
        except ValueError:
            pass
        else:
            raise AssertionError(term)


def test_backoff_max_is_capped_and_fails_closed_after_reconnect_limit() -> None:
    adapter = XRPLReadOnlyWebSocketAdapter(FailingClient(), max_reconnects=10, base_backoff_seconds=30.0)

    for _ in range(10):
        adapter.connect()

    assert adapter.backoff_seconds <= 60.0
    assert adapter.connect() is False
    assert adapter.reason == "MAX_RECONNECTS_EXCEEDED"


def test_ingestion_status_api_contract_field_names() -> None:
    from fastapi.testclient import TestClient
    from app.main import create_app

    body = TestClient(create_app()).get("/live/ingestion/status").json()

    assert list(body.keys()) == [
        "connected",
        "latest_ledger_index",
        "latest_validated_ledger_index",
        "last_snapshot_at",
        "stale_snapshot_count",
        "rejected_snapshot_count",
        "reconnect_count",
        "backoff_seconds",
        "reason",
        "ingestion_enabled",
        "ingestion_mode",
        "ingestion_source",
        "snapshot_rate_per_sec",
        "snapshot_count",
        "last_snapshot_latency_ms",
        "ledger_gap_detected",
        "ledger_gap_count",
        "duplicate_ledger_count",
        "throttled_snapshot_count",
        "unfunded_liquidity_estimate",
        "snapshot_rejection_rate",
        "is_live",
        "is_shadow",
        "is_advisory",
        "is_executable",
        "xrpl_warning",
    ]
