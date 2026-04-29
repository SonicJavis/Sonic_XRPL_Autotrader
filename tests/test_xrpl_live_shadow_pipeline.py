from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.live.xrpl_ingestion_models import XRPLLedgerEvent
from app.live.xrpl_live_shadow_pipeline import (
    LiveDriftDetector,
    XRPLLedgerSequencer,
    XRPLLiveShadowPipeline,
)
from app.validation.xrpl_validation_models import XRPLValidationResult


BASE = datetime(2026, 4, 29, 12, 0, tzinfo=timezone.utc)


def test_out_of_order_ledgers_are_processed_sequentially() -> None:
    sequencer = XRPLLedgerSequencer(initial_expected_ledger=100, max_gap_ledgers=2)

    first = sequencer.ingest(_ledger(101), processing_time=BASE + timedelta(seconds=5))
    second = sequencer.ingest(_ledger(100), processing_time=BASE + timedelta(seconds=6))

    assert first == []
    assert [item.to_dict()["ledger_index"] for item in second] == [100, 101]


def test_duplicate_ledger_is_idempotent() -> None:
    sequencer = XRPLLedgerSequencer(initial_expected_ledger=100)

    first = sequencer.ingest(_ledger(100), processing_time=BASE)
    second = sequencer.ingest(_ledger(100), processing_time=BASE + timedelta(seconds=1))

    assert [item.to_dict()["ledger_index"] for item in first] == [100]
    assert second == []
    assert sequencer.duplicate_ledger_count == 1


def test_missing_ledger_emits_gap_without_fabrication() -> None:
    sequencer = XRPLLedgerSequencer(initial_expected_ledger=100, max_gap_ledgers=1)

    emitted = sequencer.ingest(_ledger(102), processing_time=BASE + timedelta(seconds=8))

    assert [item.to_dict()["event_type"] for item in emitted] == ["GAP", "LEDGER"]
    assert emitted[0].to_dict()["missing_from"] == 100
    assert emitted[0].to_dict()["missing_to"] == 101
    assert emitted[1].to_dict()["ledger_index"] == 102


def test_pipeline_snapshot_determinism_and_partial_window_resolution() -> None:
    snapshots = {idx: _snapshot(idx, observed_fill=50.0 + idx) for idx in range(1, 5)}
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: snapshots.get(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1),
        window_size=2,
        now_provider=lambda: BASE + timedelta(seconds=20),
    )

    outputs = []
    for idx in range(1, 4):
        outputs.extend(pipeline.ingest_ledger_event(_ledger(idx), processing_time=BASE + timedelta(seconds=idx * 4)))

    assert [row["status"] for row in outputs] == ["PROCESSED", "PROCESSED", "PROCESSED"]
    assert pipeline.status()["resolved_window_count"] == 1
    assert pipeline.metrics_body()["sample_count"] == 1
    assert pipeline.metrics_body()["rolling_brier"] >= 0.0
    assert pipeline.ingest_ledger_event(_ledger(1), processing_time=BASE + timedelta(seconds=30)) == []


def test_latency_metrics_use_processing_time_only_for_observability() -> None:
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=10),
        now_provider=lambda: BASE + timedelta(seconds=100),
    )

    pipeline.ingest_ledger_event(_ledger(10, close_time=BASE), processing_time=BASE + timedelta(seconds=4), network_head=12)
    status = pipeline.status()

    assert status["ledger_lag"] == 2
    assert status["latency"]["ingestion_latency_ms"]["p50"] == 4000.0
    assert status["latency"]["processing_latency_ms"]["p50"] == 0.0


def test_gap_expires_partial_windows() -> None:
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1, max_gap_ledgers=1),
        window_size=3,
    )

    pipeline.ingest_ledger_event(_ledger(1), processing_time=BASE)
    pipeline.ingest_ledger_event(_ledger(5), processing_time=BASE + timedelta(seconds=20))

    assert pipeline.status()["gap_count"] == 1
    assert pipeline.status()["expired_window_count"] == 1


def test_drift_detection_is_stable() -> None:
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index, observed_fill=0.0),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1),
        window_size=1,
    )
    for idx in range(1, 3):
        pipeline.ingest_ledger_event(_ledger(idx), processing_time=BASE + timedelta(seconds=idx * 4))
    pipeline.replay_results = list(pipeline.live_results)

    first = pipeline.drift()
    second = LiveDriftDetector().compare(live=pipeline.live_results, replay=pipeline.replay_results)

    assert first == second
    assert first["drift_flag"] is False
    assert 0.0 <= first["drift_magnitude"] <= 1.0


def test_unvalidated_events_are_isolated_from_pipeline() -> None:
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1),
    )

    assert pipeline.ingest_ledger_event(_ledger(1, validated=False), processing_time=BASE) == []
    assert pipeline.status()["processed_ledger_count"] == 0
    assert pipeline.status()["dropped_event_count"] == 1


def test_bounded_memory_under_large_burst_and_duplicates() -> None:
    sequencer = XRPLLedgerSequencer(initial_expected_ledger=1, max_buffer_size=5, max_processed_ledgers=10)
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=sequencer,
        window_size=2,
    )

    for idx in range(1, 101):
        pipeline.ingest_ledger_event(_ledger(idx), processing_time=BASE + timedelta(milliseconds=idx))
        pipeline.ingest_ledger_event(_ledger(idx), processing_time=BASE + timedelta(milliseconds=idx + 1))

    status = pipeline.status()
    assert status["buffer_size"] <= 5
    assert len(sequencer.processed_ledgers) <= 10
    assert status["duplicate_ledger_count"] == 100
    assert status["health_state"] in {"OK", "IDLE", "NO_SNAPSHOT"}


def test_buffer_overflow_is_bounded_and_tracked() -> None:
    sequencer = XRPLLedgerSequencer(initial_expected_ledger=1, max_buffer_size=3, max_gap_ledgers=100)
    for idx in range(10, 20):
        sequencer.ingest(_ledger(idx), processing_time=BASE)

    assert len(sequencer.buffer) <= 3
    assert sequencer.dropped_event_count >= 1


def test_latency_sanitizes_negative_and_non_datetime_inputs() -> None:
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1),
        now_provider=lambda: BASE,
    )

    pipeline.ingest_ledger_event(_ledger(1, close_time=BASE + timedelta(seconds=10)), processing_time=BASE)
    status = pipeline.status()

    assert status["latency"]["ingestion_latency_ms"] == {"p50": 0.0, "p95": 0.0, "max": 0.0}
    assert status["latency"]["end_to_end_latency_ms"]["max"] == 0.0


def test_processing_time_does_not_change_validation_score() -> None:
    fast = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1),
        window_size=1,
        now_provider=lambda: BASE,
    )
    slow = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: _snapshot(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(initial_expected_ledger=1),
        window_size=1,
        now_provider=lambda: BASE + timedelta(seconds=10),
    )

    for idx in (1, 2):
        fast.ingest_ledger_event(_ledger(idx), processing_time=BASE)
        slow.ingest_ledger_event(_ledger(idx), processing_time=BASE + timedelta(seconds=100))

    assert fast.metrics_body()["rolling_brier"] == slow.metrics_body()["rolling_brier"]
    assert fast.metrics_body()["rolling_disagreement"] == slow.metrics_body()["rolling_disagreement"]


def test_drift_detector_edge_cases_are_bounded() -> None:
    detector = LiveDriftDetector(threshold=0.2)
    high = _result(1, disagreement=0.8, brier=0.7, attribution="competition")
    low = _result(2, disagreement=0.1, brier=0.05, attribution="latency")

    empty = detector.compare(live=[], replay=[])
    live_only = detector.compare(live=[high], replay=[])
    replay_only = detector.compare(live=[], replay=[high])
    spike = detector.compare(live=[high], replay=[low])

    assert empty["drift_flag"] is False
    for body in (empty, live_only, replay_only, spike):
        assert 0.0 <= body["drift_magnitude"] <= 1.0
        assert body["is_shadow"] is True
        assert body["is_executable"] is False
    assert spike["drift_flag"] is True


def _ledger(index: int, *, close_time: datetime | None = None, validated: bool = True) -> XRPLLedgerEvent:
    return XRPLLedgerEvent(
        ledger_index=index,
        ledger_hash=f"h{index}",
        close_time=close_time or BASE + timedelta(seconds=index * 4),
        validated=validated,
        raw={"type": "ledgerClosed"},
    )


def _snapshot(index: int, *, observed_fill: float = 75.0) -> ShadowSnapshotInput:
    return ShadowSnapshotInput(
        token_id=1,
        issuer="rIssuer",
        currency="USD",
        ledger_index=index,
        snapshot_price=1.0 + index * 0.001,
        execution_price_proxy=1.0 + index * 0.001,
        requested_size=100.0,
        snapshot_derived_liquidity=120.0,
        observed_possible_fill=observed_fill,
        path_complexity=1,
        route_instability=0.1,
        competition_penalty=0.1,
        slippage_estimate=0.01,
        observed_at=BASE + timedelta(seconds=index * 4),
        snapshot_quality_score=0.9,
        ledger_latency_proxy=100.0,
    )


def _result(decision_id: int, *, disagreement: float, brier: float, attribution: str) -> XRPLValidationResult:
    return XRPLValidationResult(
        decision_id=decision_id,
        fill_probability_error=0.0,
        effective_size_error=0.0,
        ev_error=0.0,
        liquidity_disappearance=0.0,
        path_failure_rate=0.0,
        competition_miss_rate=0.0,
        latency_miss=0.0,
        regime_mismatch=False,
        disagreement_score=disagreement,
        brier_score=brier,
        overconfidence_flag=False,
        underconfidence_flag=False,
        confidence_error=0.0,
        error_attribution=attribution,
    )
