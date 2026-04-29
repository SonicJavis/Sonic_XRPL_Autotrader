from fastapi.testclient import TestClient

from app.live.xrpl_ingestion_models import XRPLIngestionHealth
from app.main import create_app


class FakeIngestion:
    def __init__(self):
        self.calls = 0

    def health(self):
        self.calls += 1
        return XRPLIngestionHealth(connected=True, latest_ledger_index=10, latest_validated_ledger_index=9, reason="OK")


def test_live_ingestion_status_safe_when_not_configured() -> None:
    body = TestClient(create_app()).get("/live/ingestion/status").json()

    assert body["is_live"] is True
    assert body["is_shadow"] is True
    assert body["is_advisory"] is True
    assert body["is_executable"] is False
    assert body["connected"] is False
    assert body["reason"] == "INGESTION_NOT_CONFIGURED"


def test_live_ingestion_status_uses_adapter_without_mutating_get_state() -> None:
    app = create_app()
    adapter = FakeIngestion()
    app.state.xrpl_ingestion_adapter = adapter
    client = TestClient(app)

    first = client.get("/live/ingestion/status").json()
    second = client.get("/live/ingestion/status").json()

    assert first == second
    assert adapter.calls == 2
    assert first["connected"] is True
    assert first["is_executable"] is False


def test_live_ingestion_status_contract_fields_present() -> None:
    body = TestClient(create_app()).get("/live/ingestion/status").json()
    expected = {
        "is_live",
        "is_shadow",
        "is_advisory",
        "is_executable",
        "connected",
        "latest_ledger_index",
        "latest_validated_ledger_index",
        "last_snapshot_at",
        "stale_snapshot_count",
        "rejected_snapshot_count",
        "reconnect_count",
        "backoff_seconds",
        "reason",
        "xrpl_warning",
    }
    phase19_fields = {
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
    }
    assert expected | phase19_fields == set(body)
