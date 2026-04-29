from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from math import isfinite
from statistics import mean
from typing import Callable, Iterable, Mapping

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.live.xrpl_ingestion_models import XRPLLedgerEvent
from app.validation.xrpl_validation_engine import compare_prediction_to_window
from app.validation.xrpl_validation_models import XRPLObservedOutcomeWindow, XRPLShadowPrediction, XRPLValidationResult


LIVE_SHADOW_WARNING = (
    "Read-only live XRPL observability; validation remains probabilistic, advisory, and non-executing"
)


def _utc(raw: object) -> datetime:
    if isinstance(raw, datetime):
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


def _unit(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, min(1.0, _finite(raw, default=default)))


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(max(0.0, _finite(value)) for value in values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percentile))))
    return round(ordered[index], 6)


@dataclass(frozen=True, slots=True)
class LiveLedgerFrame:
    ledger_index: int
    ledger_time: datetime
    processing_time: datetime
    event_type: str = "LEDGER"

    def to_dict(self) -> dict[str, object]:
        return {
            "ledger_index": int(self.ledger_index),
            "ledger_time": self.ledger_time.isoformat(),
            "processing_time": self.processing_time.isoformat(),
            "event_type": self.event_type,
        }


@dataclass(frozen=True, slots=True)
class LedgerGapEvent:
    missing_from: int
    missing_to: int
    processing_time: datetime
    event_type: str = "GAP"

    def to_dict(self) -> dict[str, object]:
        return {
            "missing_from": int(self.missing_from),
            "missing_to": int(self.missing_to),
            "processing_time": self.processing_time.isoformat(),
            "event_type": self.event_type,
        }


class XRPLLedgerSequencer:
    def __init__(
        self,
        *,
        max_buffer_size: int = 32,
        max_gap_ledgers: int = 1,
        initial_expected_ledger: int | None = None,
        max_processed_ledgers: int = 4096,
    ) -> None:
        self.max_buffer_size = max(1, int(max_buffer_size))
        self.max_gap_ledgers = max(1, int(max_gap_ledgers))
        self.max_processed_ledgers = max(1, int(max_processed_ledgers))
        self.buffer: dict[int, LiveLedgerFrame] = {}
        self.expected_ledger: int | None = None if initial_expected_ledger is None else max(1, int(initial_expected_ledger))
        self.processed_ledgers: set[int] = set()
        self._processed_order: list[int] = []
        self.duplicate_ledger_count = 0
        self.gap_count = 0
        self.dropped_event_count = 0

    def ingest(self, event: XRPLLedgerEvent, *, processing_time: datetime) -> list[LiveLedgerFrame | LedgerGapEvent]:
        processing_time = _utc(processing_time)
        if not bool(event.validated):
            self.dropped_event_count += 1
            return []
        ledger_index = max(0, int(event.ledger_index))
        if ledger_index <= 0:
            self.dropped_event_count += 1
            return []
        if ledger_index in self.processed_ledgers or ledger_index in self.buffer:
            self.duplicate_ledger_count += 1
            return []
        if self.expected_ledger is not None and ledger_index < self.expected_ledger:
            self.duplicate_ledger_count += 1
            return []
        self.buffer[ledger_index] = LiveLedgerFrame(
            ledger_index=ledger_index,
            ledger_time=_utc(event.close_time),
            processing_time=processing_time,
        )
        return self._drain_ready(processing_time)

    def _drain_ready(self, processing_time: datetime) -> list[LiveLedgerFrame | LedgerGapEvent]:
        emitted: list[LiveLedgerFrame | LedgerGapEvent] = []
        if self.expected_ledger is None and self.buffer:
            self.expected_ledger = min(self.buffer)
        while self.expected_ledger is not None:
            if self.expected_ledger in self.buffer:
                frame = self.buffer.pop(self.expected_ledger)
                self._mark_processed(frame.ledger_index)
                emitted.append(frame)
                self.expected_ledger += 1
                continue
            if not self.buffer:
                break
            next_available = min(self.buffer)
            gap_width = next_available - self.expected_ledger
            if gap_width >= self.max_gap_ledgers:
                gap = LedgerGapEvent(
                    missing_from=self.expected_ledger,
                    missing_to=next_available - 1,
                    processing_time=processing_time,
                )
                self.gap_count += 1
                emitted.append(gap)
                self.expected_ledger = next_available
                continue
            break
        while len(self.buffer) > self.max_buffer_size:
            self.buffer.pop(max(self.buffer))
            self.dropped_event_count += 1
        return emitted

    def _mark_processed(self, ledger_index: int) -> None:
        self.processed_ledgers.add(ledger_index)
        self._processed_order.append(ledger_index)
        while len(self._processed_order) > self.max_processed_ledgers:
            expired = self._processed_order.pop(0)
            self.processed_ledgers.discard(expired)


@dataclass(slots=True)
class PartialOutcomeWindow:
    token_id: int
    issuer: str
    start_ledger: int
    target_end_ledger: int
    samples: list[ShadowSnapshotInput] = field(default_factory=list)
    state: str = "pending"

    def advance(self, snapshot: ShadowSnapshotInput) -> None:
        if self.state != "pending":
            return
        if int(snapshot.ledger_index) <= self.start_ledger:
            return
        if int(snapshot.token_id) != self.token_id or str(snapshot.issuer) != self.issuer:
            return
        self.samples.append(snapshot)
        if int(snapshot.ledger_index) >= self.target_end_ledger:
            self.state = "resolved"

    def expire_for_gap(self) -> None:
        if self.state == "pending":
            self.state = "expired"

    def to_outcome(self) -> XRPLObservedOutcomeWindow | None:
        if self.state != "resolved" or not self.samples:
            return None
        fills = [max(0.0, _finite(sample.observed_possible_fill)) for sample in self.samples]
        first_price = max(0.0, _finite(self.samples[0].snapshot_price))
        drifts = [
            0.0 if first_price <= 0.0 else (_finite(sample.snapshot_price) - first_price) / max(first_price, 1e-9)
            for sample in self.samples
        ]
        return XRPLObservedOutcomeWindow(
            token_id=self.token_id,
            issuer=self.issuer,
            start_ledger=self.start_ledger + 1,
            end_ledger=self.samples[-1].ledger_index,
            max_possible_fill=max(fills),
            min_possible_fill=min(fills),
            avg_possible_fill=mean(fills),
            liquidity_decay_curve=[_unit(fill / max(_finite(sample.snapshot_derived_liquidity), 1e-9)) for fill, sample in zip(fills, self.samples)],
            price_drift_curve=drifts,
            route_changes_count=sum(1 for sample in self.samples if _finite(sample.route_instability) >= 0.5),
            competition_events_proxy=max(_unit(sample.competition_penalty) for sample in self.samples),
            latency_distribution_ms=[max(0.0, _finite(sample.ledger_latency_proxy)) for sample in self.samples],
            observed_at=self.samples[-1].observed_at,
        )


class PartialOutcomeWindowTracker:
    def __init__(self, *, window_size: int = 3) -> None:
        self.window_size = max(1, int(window_size))
        self.pending: list[tuple[XRPLShadowPrediction, PartialOutcomeWindow]] = []
        self.resolved: list[XRPLValidationResult] = []
        self.expired_count = 0

    def start(self, prediction: XRPLShadowPrediction) -> None:
        self.pending.append(
            (
                prediction,
                PartialOutcomeWindow(
                    token_id=prediction.token_id,
                    issuer=prediction.issuer,
                    start_ledger=prediction.ledger_index_start,
                    target_end_ledger=prediction.ledger_index_start + self.window_size,
                ),
            )
        )

    def advance(self, snapshot: ShadowSnapshotInput) -> list[XRPLValidationResult]:
        results: list[XRPLValidationResult] = []
        remaining: list[tuple[XRPLShadowPrediction, PartialOutcomeWindow]] = []
        for prediction, window in self.pending:
            window.advance(snapshot)
            outcome = window.to_outcome()
            if outcome is None:
                remaining.append((prediction, window))
                continue
            result = compare_prediction_to_window(prediction, outcome)
            results.append(result)
            self.resolved.append(result)
        self.pending = remaining
        return results

    def expire_for_gap(self) -> None:
        self.expired_count += len(self.pending)
        for _, window in self.pending:
            window.expire_for_gap()
        self.pending = []


@dataclass(slots=True)
class LiveShadowMetrics:
    current_ledger: int = 0
    buffer_size: int = 0
    ledger_lag: int = 0
    health_state: str = "IDLE"
    processed_ledger_count: int = 0
    duplicate_ledger_count: int = 0
    gap_count: int = 0
    dropped_event_count: int = 0
    pending_window_count: int = 0
    resolved_window_count: int = 0
    expired_window_count: int = 0
    ingestion_latency_ms: list[float] = field(default_factory=list)
    processing_latency_ms: list[float] = field(default_factory=list)
    end_to_end_latency_ms: list[float] = field(default_factory=list)
    brier_scores: list[float] = field(default_factory=list)
    disagreement_scores: list[float] = field(default_factory=list)
    attribution_counts: dict[str, int] = field(default_factory=dict)

    def status(self) -> dict[str, object]:
        return {
            "current_ledger": int(self.current_ledger),
            "buffer_size": int(self.buffer_size),
            "ledger_lag": int(self.ledger_lag),
            "health_state": self.health_state,
            "processed_ledger_count": int(self.processed_ledger_count),
            "duplicate_ledger_count": int(self.duplicate_ledger_count),
            "gap_count": int(self.gap_count),
            "dropped_event_count": int(self.dropped_event_count),
            "pending_window_count": int(self.pending_window_count),
            "resolved_window_count": int(self.resolved_window_count),
            "expired_window_count": int(self.expired_window_count),
            "latency": self.latency_summary(),
            **_meta(),
        }

    def metric_body(self) -> dict[str, object]:
        count = len(self.brier_scores)
        return {
            "rolling_brier": 0.0 if count == 0 else round(mean(self.brier_scores), 6),
            "rolling_disagreement": 0.0 if not self.disagreement_scores else round(mean(self.disagreement_scores), 6),
            "attribution_breakdown": dict(sorted(self.attribution_counts.items())),
            "sample_count": count,
            **_meta(),
        }

    def latency_summary(self) -> dict[str, object]:
        return {
            "ingestion_latency_ms": _latency_stats(self.ingestion_latency_ms),
            "processing_latency_ms": _latency_stats(self.processing_latency_ms),
            "end_to_end_latency_ms": _latency_stats(self.end_to_end_latency_ms),
        }


class LiveDriftDetector:
    def __init__(self, *, threshold: float = 0.20) -> None:
        self.threshold = max(0.0, _finite(threshold, default=0.20))

    def compare(self, *, live: Iterable[XRPLValidationResult], replay: Iterable[XRPLValidationResult]) -> dict[str, object]:
        live_rows = list(live)
        replay_rows = list(replay)
        live_disagreement = [row.disagreement_score for row in live_rows]
        replay_disagreement = [row.disagreement_score for row in replay_rows]
        live_brier = [row.brier_score for row in live_rows]
        replay_brier = [row.brier_score for row in replay_rows]
        attribution_shift = _distribution_shift(
            [row.error_attribution for row in live_rows],
            [row.error_attribution for row in replay_rows],
        )
        magnitude = _unit(
            abs(_avg(live_disagreement) - _avg(replay_disagreement))
            + abs(_avg(live_brier) - _avg(replay_brier))
            + attribution_shift
        )
        return {
            "drift_flag": magnitude >= self.threshold,
            "drift_magnitude": round(magnitude, 6),
            "live_sample_count": len(live_rows),
            "replay_sample_count": len(replay_rows),
            **_meta(),
        }


class XRPLLiveShadowPipeline:
    def __init__(
        self,
        *,
        snapshot_provider: Callable[[LiveLedgerFrame], ShadowSnapshotInput | None],
        prediction_provider: Callable[[ShadowSnapshotInput], XRPLShadowPrediction] | None = None,
        sequencer: XRPLLedgerSequencer | None = None,
        window_size: int = 3,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.snapshot_provider = snapshot_provider
        self.prediction_provider = prediction_provider or _default_prediction
        self.sequencer = sequencer or XRPLLedgerSequencer()
        self.window_tracker = PartialOutcomeWindowTracker(window_size=window_size)
        self.metrics = LiveShadowMetrics()
        self.now_provider = now_provider or (lambda: datetime.now(tz=timezone.utc))
        self.live_results: list[XRPLValidationResult] = []
        self.replay_results: list[XRPLValidationResult] = []

    def ingest_ledger_event(self, event: XRPLLedgerEvent, *, processing_time: datetime | None = None, network_head: int | None = None) -> list[dict[str, object]]:
        received_at = _utc(processing_time or self.now_provider())
        emitted = self.sequencer.ingest(event, processing_time=received_at)
        outputs: list[dict[str, object]] = []
        for item in emitted:
            if isinstance(item, LedgerGapEvent):
                self.window_tracker.expire_for_gap()
                self._sync_metrics(network_head=network_head)
                outputs.append(item.to_dict())
                continue
            outputs.append(self._process_frame(item, network_head=network_head))
        self._sync_metrics(network_head=network_head)
        return outputs

    def _process_frame(self, frame: LiveLedgerFrame, *, network_head: int | None) -> dict[str, object]:
        start = self.now_provider()
        snapshot = self.snapshot_provider(frame)
        if snapshot is None:
            self.metrics.health_state = "NO_SNAPSHOT"
            return {**frame.to_dict(), "status": "NO_SNAPSHOT", **_meta()}
        prediction = self.prediction_provider(snapshot)
        self.window_tracker.start(prediction)
        results = self.window_tracker.advance(snapshot)
        self.live_results.extend(results)
        for result in results:
            self.metrics.brier_scores.append(result.brier_score)
            self.metrics.disagreement_scores.append(result.disagreement_score)
            self.metrics.attribution_counts[result.error_attribution] = self.metrics.attribution_counts.get(result.error_attribution, 0) + 1
        end = self.now_provider()
        ingestion_latency = max(0.0, (frame.processing_time - frame.ledger_time).total_seconds() * 1000.0)
        processing_latency = max(0.0, (end - start).total_seconds() * 1000.0)
        self.metrics.ingestion_latency_ms.append(round(ingestion_latency, 6))
        self.metrics.processing_latency_ms.append(round(processing_latency, 6))
        self.metrics.end_to_end_latency_ms.append(round(ingestion_latency + processing_latency, 6))
        self.metrics.current_ledger = frame.ledger_index
        self.metrics.health_state = "OK"
        self.metrics.ledger_lag = max(0, int(network_head or frame.ledger_index) - frame.ledger_index)
        return {
            **frame.to_dict(),
            "status": "PROCESSED",
            "snapshot": _snapshot_dict(snapshot),
            "validation_results": [row.to_dict() for row in results],
            **_meta(),
        }

    def status(self) -> dict[str, object]:
        self._sync_metrics(network_head=None)
        return self.metrics.status()

    def metrics_body(self) -> dict[str, object]:
        return self.metrics.metric_body()

    def drift(self) -> dict[str, object]:
        return LiveDriftDetector().compare(live=self.live_results, replay=self.replay_results)

    def to_report(self) -> dict[str, object]:
        status = self.status()
        metrics = self.metrics_body()
        drift = self.drift()
        return {
            "status": status,
            "metrics": metrics,
            "drift": drift,
            "gap_count": status["gap_count"],
            "duplicate_count": status["duplicate_ledger_count"],
            "pending_windows": status["pending_window_count"],
            "resolved_windows": status["resolved_window_count"],
            "expired_windows": status["expired_window_count"],
            **_meta(),
        }

    def _sync_metrics(self, *, network_head: int | None) -> None:
        self.metrics.buffer_size = len(self.sequencer.buffer)
        self.metrics.processed_ledger_count = len(self.sequencer.processed_ledgers)
        self.metrics.duplicate_ledger_count = self.sequencer.duplicate_ledger_count
        self.metrics.gap_count = self.sequencer.gap_count
        self.metrics.dropped_event_count = self.sequencer.dropped_event_count
        self.metrics.pending_window_count = len(self.window_tracker.pending)
        self.metrics.resolved_window_count = len(self.window_tracker.resolved)
        self.metrics.expired_window_count = self.window_tracker.expired_count
        if network_head is not None:
            self.metrics.ledger_lag = max(0, int(network_head) - int(self.metrics.current_ledger))


def default_live_status() -> dict[str, object]:
    return LiveShadowMetrics(health_state="NOT_CONFIGURED").status()


def default_live_metrics() -> dict[str, object]:
    return LiveShadowMetrics(health_state="NOT_CONFIGURED").metric_body()


def default_live_drift() -> dict[str, object]:
    return LiveDriftDetector().compare(live=[], replay=[])


def _default_prediction(snapshot: ShadowSnapshotInput) -> XRPLShadowPrediction:
    requested = max(0.0, _finite(snapshot.requested_size))
    observed = max(0.0, _finite(snapshot.observed_possible_fill))
    probability = _unit(observed / max(requested, 1e-9))
    return XRPLShadowPrediction(
        decision_id=int(snapshot.ledger_index),
        token_id=int(snapshot.token_id),
        issuer=str(snapshot.issuer),
        ledger_index_start=int(snapshot.ledger_index),
        predicted_probability=probability,
        predicted_effective_size=observed,
        predicted_ev=observed - requested,
        predicted_path_complexity=int(snapshot.path_complexity),
        predicted_route_instability=_unit(snapshot.route_instability),
        predicted_competition_penalty=_unit(snapshot.competition_penalty),
        predicted_regime="STABLE_SHADOW" if probability > 0.0 else "EXECUTION_COLLAPSE",
        predicted_confidence=max(0.0, min(1.0, 1.0 - _unit(snapshot.route_instability))),
        created_at=snapshot.observed_at,
        requested_size=requested,
        predicted_liquidity=max(0.0, _finite(snapshot.snapshot_derived_liquidity)),
        predicted_latency_ms=max(0.0, _finite(snapshot.ledger_latency_proxy)),
    )


def _snapshot_dict(snapshot: ShadowSnapshotInput) -> dict[str, object]:
    data = asdict(snapshot)
    data["observed_at"] = _utc(snapshot.observed_at).isoformat()
    return data


def _latency_stats(values: list[float]) -> dict[str, float]:
    return {
        "p50": _percentile(values, 0.50),
        "p95": _percentile(values, 0.95),
        "max": round(max(values), 6) if values else 0.0,
    }


def _distribution_shift(live: list[str], replay: list[str]) -> float:
    labels = sorted(set(live) | set(replay))
    if not labels:
        return 0.0
    live_total = max(1, len(live))
    replay_total = max(1, len(replay))
    return _unit(sum(abs((live.count(label) / live_total) - (replay.count(label) / replay_total)) for label in labels) / 2.0)


def _avg(values: list[float]) -> float:
    return 0.0 if not values else mean(values)


def _meta() -> dict[str, object]:
    return {
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": LIVE_SHADOW_WARNING,
    }
