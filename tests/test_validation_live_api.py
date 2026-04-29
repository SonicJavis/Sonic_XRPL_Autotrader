from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isfinite

from fastapi.testclient import TestClient

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.live.xrpl_ingestion_models import XRPLLedgerEvent
from app.live.xrpl_live_shadow_pipeline import XRPLLedgerSequencer, XRPLLiveShadowPipeline
from app.main import create_app


BASE = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)


def test_live_validation_api_default_state_safe() -> None:
    client = TestClient(create_app())

    status = client.get("/validation/live/status").json()
    metrics = client.get("/validation/live/metrics").json()
    drift = client.get("/validation/live/drift").json()

    assert status["health_state"] == "NOT_CONFIGURED"
    assert metrics["sample_count"] == 0
    assert drift["drift_flag"] is False
    _assert_meta(status)
    _assert_meta(metrics)
    _assert_meta(drift)
    assert _finite_json(status)
    assert _finite_json(metrics)
    assert _finite_json(drift)


def test_live_validation_api_reads_attached_pipeline_without_mutation() -> None:
    app = create_app()
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1),
        window_size=1,
        now_provider=lambda: BASE + timedelta(seconds=20),
    )
    pipeline.ingest_ledger_event(_ledger(1), processing_time=BASE + timedelta(seconds=4))
    pipeline.ingest_ledger_event(_ledger(2), processing_time=BASE + timedelta(seconds=8))
    app.state.live_shadow_pipeline = pipeline
    client = TestClient(app)

    first = client.get("/validation/live/status").json()
    second = client.get("/validation/live/status").json()
    metrics = client.get("/validation/live/metrics").json()
    drift = client.get("/validation/live/drift").json()

    assert first == second
    assert first["current_ledger"] == 2
    assert metrics["sample_count"] == 1
    assert "attribution_breakdown" in metrics
    assert 0.0 <= drift["drift_magnitude"] <= 1.0
    _assert_meta(first)
    _assert_meta(metrics)
    _assert_meta(drift)


def _ledger(index: int) -> XRPLLedgerEvent:
    return XRPLLedgerEvent(
        ledger_index=index,
        ledger_hash=f"h{index}",
        close_time=BASE + timedelta(seconds=index * 4),
        validated=True,
        raw={"type": "ledgerClosed"},
    )


def _snapshot(index: int) -> ShadowSnapshotInput:
    return ShadowSnapshotInput(
        token_id=1,
        issuer="rIssuer",
        currency="USD",
        ledger_index=index,
        snapshot_price=1.0,
        execution_price_proxy=1.0,
        requested_size=100.0,
        snapshot_derived_liquidity=100.0,
        observed_possible_fill=50.0,
        path_complexity=1,
        route_instability=0.1,
        competition_penalty=0.1,
        slippage_estimate=0.01,
        observed_at=BASE + timedelta(seconds=index * 4),
        snapshot_quality_score=0.9,
        ledger_latency_proxy=100.0,
    )


def _assert_meta(body: dict[str, object]) -> None:
    assert body["is_shadow"] is True
    assert body["is_advisory"] is True
    assert body["is_executable"] is False
    assert body["is_truth"] is False


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
