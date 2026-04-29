from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from pathlib import Path
from statistics import mean
from typing import Callable, Iterable, Mapping

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.live.xrpl_ingestion_models import XRPLLedgerEvent
from app.live.xrpl_live_shadow_pipeline import XRPLLedgerSequencer, XRPLLiveShadowPipeline
from app.validation.xrpl_validation_models import XRPLValidationResult


SOAK_WARNING = "Controlled XRPL live-shadow soak output is advisory, read-only, and non-executing"


@dataclass(frozen=True, slots=True)
class NodeVarianceSnapshot:
    node_id: str
    latest_ledger_index: int
    avg_latency_ms: float
    gap_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "latest_ledger_index": max(0, int(self.latest_ledger_index)),
            "avg_latency_ms": round(_non_negative(self.avg_latency_ms), 6),
            "gap_count": max(0, int(self.gap_count)),
        }


class XRPLLiveShadowSoakRunner:
    def __init__(
        self,
        *,
        pipeline: XRPLLiveShadowPipeline,
        memory_sampler: Callable[[], float] | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.memory_sampler = memory_sampler or (lambda: 0.0)
        self.memory_samples_mb: list[float] = []

    def run(
        self,
        events: Iterable[XRPLLedgerEvent],
        *,
        processing_time_provider: Callable[[XRPLLedgerEvent], datetime] | None = None,
        network_head_provider: Callable[[XRPLLedgerEvent], int] | None = None,
        runtime_hours: float = 0.0,
    ) -> dict[str, object]:
        outputs: list[dict[str, object]] = []
        for event in events:
            processing_time = (
                processing_time_provider(event)
                if processing_time_provider is not None
                else _event_processing_time(event)
            )
            outputs.extend(
                self.pipeline.ingest_ledger_event(
                    event,
                    processing_time=processing_time,
                    network_head=None if network_head_provider is None else network_head_provider(event),
                )
            )
            self.memory_samples_mb.append(_non_negative(self.memory_sampler()))
        return build_soak_report(
            pipeline=self.pipeline,
            runtime_hours=runtime_hours,
            memory_samples_mb=self.memory_samples_mb,
            outputs=outputs,
        )


def build_soak_report(
    *,
    pipeline: XRPLLiveShadowPipeline,
    runtime_hours: float = 0.0,
    memory_samples_mb: Iterable[float] = (),
    outputs: Iterable[Mapping[str, object]] = (),
) -> dict[str, object]:
    status = pipeline.status()
    drift = pipeline.drift()
    latency_values = list(pipeline.metrics.ingestion_latency_ms)
    memory_values = [_non_negative(value) for value in memory_samples_mb]
    output_rows = list(outputs)
    return {
        "runtime_hours": round(_non_negative(runtime_hours), 6),
        "total_ledgers_processed": int(status["processed_ledger_count"]),
        "gap_events": int(status["gap_count"]),
        "duplicate_events": int(status["duplicate_ledger_count"]),
        "avg_latency": round(mean(latency_values), 6) if latency_values else 0.0,
        "max_latency": round(max(latency_values), 6) if latency_values else 0.0,
        "drift_events": 1 if bool(drift["drift_flag"]) else 0,
        "drift_magnitude": round(_unit(drift["drift_magnitude"]), 6),
        "memory_peak_mb": round(max(memory_values), 6) if memory_values else 0.0,
        "buffer_size": int(status["buffer_size"]),
        "ledger_lag": int(status["ledger_lag"]),
        "pending_windows": int(status["pending_window_count"]),
        "resolved_windows": int(status["resolved_window_count"]),
        "expired_windows": int(status["expired_window_count"]),
        "output_count": len(output_rows),
        "health_state": str(status["health_state"]),
        **_meta(),
    }


def compare_node_variance(nodes: Iterable[NodeVarianceSnapshot | Mapping[str, object]]) -> dict[str, object]:
    rows = [_node_row(node) for node in nodes]
    ledgers = [int(row["latest_ledger_index"]) for row in rows]
    latencies = [float(row["avg_latency_ms"]) for row in rows]
    gaps = [int(row["gap_count"]) for row in rows]
    return {
        "node_count": len(rows),
        "nodes": rows,
        "latest_ledger_spread": 0 if not ledgers else max(ledgers) - min(ledgers),
        "latency_spread_ms": 0.0 if not latencies else round(max(latencies) - min(latencies), 6),
        "gap_count_spread": 0 if not gaps else max(gaps) - min(gaps),
        "streams_merged": False,
        **_meta(),
    }


def load_soak_fixture(path: Path) -> tuple[XRPLLiveShadowPipeline, list[XRPLLedgerEvent], Callable[[XRPLLedgerEvent], datetime], float]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    base_time = _dt(fixture.get("base_time"))
    snapshots: dict[int, ShadowSnapshotInput | None] = {}
    for row in fixture.get("events", []):
        if not isinstance(row, dict):
            continue
        ledger_index = max(0, int(_finite(row.get("ledger_index"))))
        snapshots[ledger_index] = _snapshot(ledger_index, row.get("snapshot"), base_time)
    pipeline = XRPLLiveShadowPipeline(
        snapshot_provider=lambda frame: snapshots.get(frame.ledger_index),
        sequencer=XRPLLedgerSequencer(
            initial_expected_ledger=int(fixture.get("initial_expected_ledger", 1)),
            max_gap_ledgers=int(fixture.get("max_gap_ledgers", 1)),
            max_buffer_size=int(fixture.get("max_buffer_size", 32)),
            max_processed_ledgers=int(fixture.get("max_processed_ledgers", 4096)),
        ),
        window_size=int(fixture.get("window_size", 3)),
        now_provider=lambda: base_time,
    )
    pipeline.replay_results = [_validation(row) for row in fixture.get("replay_results", []) if isinstance(row, dict)]
    events = [_event(row, base_time) for row in fixture.get("events", []) if isinstance(row, dict)]

    def processing_time_provider(event: XRPLLedgerEvent) -> datetime:
        delay = _finite(event.raw.get("processing_delay_ms"), default=0.0)
        return base_time + timedelta(milliseconds=max(0.0, delay))

    return pipeline, events, processing_time_provider, _non_negative(fixture.get("runtime_hours", 0.0))


def run_soak_fixture(path: Path) -> dict[str, object]:
    pipeline, events, processing_time_provider, runtime_hours = load_soak_fixture(path)
    report = XRPLLiveShadowSoakRunner(pipeline=pipeline).run(
        events,
        processing_time_provider=processing_time_provider,
        network_head_provider=lambda event: int(event.raw.get("network_head", event.ledger_index)),
        runtime_hours=runtime_hours,
    )
    return {
        "fixture": str(path),
        **report,
    }


def _event(row: Mapping[str, object], base_time: datetime) -> XRPLLedgerEvent:
    ledger_index = max(0, int(_finite(row.get("ledger_index"))))
    event_type = str(row.get("type", "ledgerClosed"))
    raw = dict(row)
    raw["type"] = event_type
    return XRPLLedgerEvent(
        ledger_index=ledger_index,
        ledger_hash=None if row.get("ledger_hash") is None else str(row.get("ledger_hash")),
        close_time=base_time + timedelta(seconds=ledger_index * 4),
        validated=bool(row.get("validated", event_type == "ledgerClosed")),
        raw=raw,
    )


def _snapshot(ledger_index: int, raw: object, base_time: datetime) -> ShadowSnapshotInput | None:
    if raw is None or not isinstance(raw, Mapping):
        return None
    observed = _non_negative(raw.get("observed_possible_fill", 75.0))
    liquidity = max(observed, _non_negative(raw.get("snapshot_derived_liquidity", 100.0)))
    return ShadowSnapshotInput(
        token_id=max(0, int(_finite(raw.get("token_id", 1), default=1.0))),
        issuer=str(raw.get("issuer", "rIssuer")),
        currency=str(raw.get("currency", "USD")),
        ledger_index=ledger_index,
        snapshot_price=_non_negative(raw.get("snapshot_price", 1.0 + ledger_index * 0.001)),
        execution_price_proxy=_non_negative(raw.get("execution_price_proxy", 1.0 + ledger_index * 0.001)),
        requested_size=_non_negative(raw.get("requested_size", 100.0)),
        snapshot_derived_liquidity=liquidity,
        observed_possible_fill=min(observed, liquidity),
        path_complexity=max(0, int(_finite(raw.get("path_complexity", 1), default=1.0))),
        route_instability=_unit(raw.get("route_instability", 0.1)),
        competition_penalty=_unit(raw.get("competition_penalty", 0.1)),
        slippage_estimate=_non_negative(raw.get("slippage_estimate", 0.01)),
        observed_at=base_time + timedelta(seconds=ledger_index * 4),
        snapshot_quality_score=_unit(raw.get("snapshot_quality_score", 0.9), default=0.9),
        ledger_latency_proxy=_non_negative(raw.get("ledger_latency_proxy", 100.0)),
    )


def _validation(row: Mapping[str, object]) -> XRPLValidationResult:
    return XRPLValidationResult(
        decision_id=int(_finite(row.get("decision_id", 0))),
        fill_probability_error=0.0,
        effective_size_error=0.0,
        ev_error=0.0,
        liquidity_disappearance=0.0,
        path_failure_rate=0.0,
        competition_miss_rate=0.0,
        latency_miss=0.0,
        regime_mismatch=False,
        disagreement_score=_unit(row.get("disagreement_score", 0.0)),
        brier_score=_unit(row.get("brier_score", 0.0)),
        overconfidence_flag=False,
        underconfidence_flag=False,
        confidence_error=0.0,
        error_attribution=str(row.get("error_attribution", "unknown")),
    )


def _node_row(node: NodeVarianceSnapshot | Mapping[str, object]) -> dict[str, object]:
    if isinstance(node, NodeVarianceSnapshot):
        return node.to_dict()
    return NodeVarianceSnapshot(
        node_id=str(node.get("node_id", "")),
        latest_ledger_index=int(_finite(node.get("latest_ledger_index", 0))),
        avg_latency_ms=_non_negative(node.get("avg_latency_ms", 0.0)),
        gap_count=int(_finite(node.get("gap_count", 0))),
    ).to_dict()


def _event_processing_time(event: XRPLLedgerEvent) -> datetime:
    return (event.close_time or datetime.fromtimestamp(0, tz=timezone.utc)) + timedelta(
        milliseconds=_non_negative(event.raw.get("processing_delay_ms", 0.0))
    )


def _dt(raw: object) -> datetime:
    if isinstance(raw, str):
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            value = datetime.fromtimestamp(0, tz=timezone.utc)
    elif isinstance(raw, datetime):
        value = raw
    else:
        value = datetime.fromtimestamp(0, tz=timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _finite(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _non_negative(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, _finite(raw, default=default))


def _unit(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, min(1.0, _finite(raw, default=default)))


def _meta() -> dict[str, object]:
    return {
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": SOAK_WARNING,
    }
