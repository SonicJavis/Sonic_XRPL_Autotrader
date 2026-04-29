from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from math import isfinite
from pathlib import Path

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.live.xrpl_ingestion_models import XRPLLedgerEvent
from app.live.xrpl_live_shadow_pipeline import XRPLLedgerSequencer, XRPLLiveShadowPipeline
from app.live.xrpl_live_soak import (
    NodeVarianceSnapshot,
    XRPLLiveShadowSoakRunner,
    compare_node_variance,
    run_soak_fixture,
)


BASE = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)
FIXTURE = Path("data/live_shadow_replay_fixtures/phase23_2_soak.json")


def test_soak_fixture_report_is_deterministic_and_finite() -> None:
    first = run_soak_fixture(FIXTURE)
    second = run_soak_fixture(FIXTURE)

    assert first == second
    assert first["total_ledgers_processed"] >= 1
    assert first["gap_events"] >= 1
    assert first["duplicate_events"] >= 1
    assert first["memory_peak_mb"] == 0.0
    assert first["is_shadow"] is True
    assert first["is_executable"] is False
    assert _finite_json(first)


def test_soak_runner_tracks_memory_peak_and_bounded_buffer() -> None:
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1, max_buffer_size=3, max_processed_ledgers=5),
        window_size=1,
        now_provider=lambda: BASE,
    )
    samples = iter([10.0, 20.0, 15.0, 25.0])
    runner = XRPLLiveShadowSoakRunner(pipeline=pipeline, memory_sampler=lambda: next(samples, 25.0))

    report = runner.run([_ledger(1), _ledger(2), _ledger(2), _ledger(5)], runtime_hours=0.01)

    assert report["memory_peak_mb"] == 25.0
    assert report["buffer_size"] <= 3
    assert report["duplicate_events"] == 1
    assert report["gap_events"] >= 1
    assert report["runtime_hours"] == 0.01
    assert _finite_json(report)


def test_non_ledgerclosed_events_do_not_enter_soak_processing() -> None:
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=10),
        window_size=1,
    )
    runner = XRPLLiveShadowSoakRunner(pipeline=pipeline)

    report = runner.run(
        [
            _ledger(10, event_type="transaction", validated=True),
            _ledger(10, event_type="ledgerClosed", validated=True),
        ]
    )

    assert report["total_ledgers_processed"] == 1
    assert pipeline.status()["dropped_event_count"] == 1


def test_multi_node_variance_is_observability_only_and_does_not_merge_streams() -> None:
    body = compare_node_variance(
        [
            NodeVarianceSnapshot("node-a", latest_ledger_index=100, avg_latency_ms=120.0, gap_count=1),
            {"node_id": "node-b", "latest_ledger_index": 103, "avg_latency_ms": 250.0, "gap_count": 3},
        ]
    )

    assert body["node_count"] == 2
    assert body["latest_ledger_spread"] == 3
    assert body["latency_spread_ms"] == 130.0
    assert body["gap_count_spread"] == 2
    assert body["streams_merged"] is False
    assert body["is_advisory"] is True
    assert body["is_executable"] is False


def test_soak_cli_runs_offline_and_returns_stable_json() -> None:
    cmd = [sys.executable, "scripts/xrpl_live_shadow_soak.py", "--fixture", str(FIXTURE)]
    first = subprocess.run(cmd, check=True, capture_output=True, text=True)
    second = subprocess.run(cmd, check=True, capture_output=True, text=True)

    assert first.stdout == second.stdout
    body = json.loads(first.stdout)
    assert body["fixture"] == str(FIXTURE)
    assert body["is_shadow"] is True
    assert body["is_executable"] is False
    assert _finite_json(body)


def _ledger(index: int, *, event_type: str = "ledgerClosed", validated: bool = True) -> XRPLLedgerEvent:
    return XRPLLedgerEvent(
        ledger_index=index,
        ledger_hash=f"h{index}",
        close_time=BASE + timedelta(seconds=index * 4),
        validated=validated,
        raw={"type": event_type},
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


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
