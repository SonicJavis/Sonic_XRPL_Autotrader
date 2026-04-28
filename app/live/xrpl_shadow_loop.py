from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from math import isfinite

from app.calibration.xrpl_memory_model import XRPLMemoryAggregate
from app.calibration.xrpl_regime_detector import XRPLRegimeAssessment, XRPLRegimeDetector
from app.calibration.xrpl_time_execution_model import XRPLTimeExecutionInput, XRPLTimeExecutionModel, XRPLTimeExecutionResult
from app.db.models import ShadowDecisionRecord
from app.decision.xrpl_memory_weighting import XRPLMemoryWeighting, XRPLMemoryWeightingInput, XRPLMemoryWeightingResult
from app.decision.xrpl_trade_gate import XRPLTradeGate, XRPLTradeGateDecision, XRPLTradeGateInput
from app.live.shadow_snapshot_source import ShadowSnapshotInput, ShadowSnapshotSource

logger = logging.getLogger(__name__)


def _finite_float(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def _clamp_unit(raw: object) -> float:
    return max(0.0, min(1.0, _finite_float(raw)))


def _risk_level(score: float) -> str:
    score = _clamp_unit(score)
    if score >= 0.85:
        return "CRITICAL"
    if score >= 0.60:
        return "HIGH"
    if score >= 0.30:
        return "MEDIUM"
    return "LOW"


@dataclass(slots=True)
class XRPLShadowTickResult:
    stored: bool
    record: ShadowDecisionRecord | None
    reason: str


class XRPLShadowLoop:
    """Deterministic read-only shadow validation loop for advisory XRPL decisions."""

    def __init__(
        self,
        *,
        session_factory,
        snapshot_source: ShadowSnapshotSource,
        trade_gate: XRPLTradeGate | None = None,
        memory_weighting: XRPLMemoryWeighting | None = None,
        regime_detector: XRPLRegimeDetector | None = None,
        time_model: XRPLTimeExecutionModel | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.snapshot_source = snapshot_source
        self.trade_gate = trade_gate or XRPLTradeGate()
        self.memory_weighting = memory_weighting or XRPLMemoryWeighting()
        self.regime_detector = regime_detector or XRPLRegimeDetector()
        self.time_model = time_model or XRPLTimeExecutionModel()

    def run_tick(self) -> XRPLShadowTickResult:
        snapshot = self.snapshot_source.next_snapshot()
        if snapshot is None:
            return XRPLShadowTickResult(stored=False, record=None, reason="NO_SNAPSHOT_AVAILABLE")
        record = self.build_shadow_decision(snapshot)
        if not self._is_valid_record(record):
            logger.info(
                "shadow_tick_rejected token_id=%s regime=%s probability=%.6f blocked=%s",
                record.token_id,
                record.regime,
                record.memory_adjusted_probability,
                True,
            )
            return XRPLShadowTickResult(stored=False, record=None, reason="INVALID_SHADOW_RECORD")
        persisted = self.persist_shadow_decision(record)
        logger.info(
            "shadow_tick token_id=%s regime=%s probability=%.6f blocked=%s",
            persisted.token_id,
            persisted.regime,
            persisted.memory_adjusted_probability,
            persisted.memory_adjusted_probability <= 0.0
            or persisted.memory_adjusted_effective_size <= 0.0
            or persisted.drift_adjusted_ev <= 0.0,
        )
        return XRPLShadowTickResult(stored=True, record=persisted, reason="STORED")

    def run_n_ticks(self, n: int) -> list[XRPLShadowTickResult]:
        return [self.run_tick() for _ in range(max(0, int(n)))]

    def build_shadow_decision(self, snapshot: ShadowSnapshotInput) -> ShadowDecisionRecord:
        time_result = self.time_model.evaluate(
            XRPLTimeExecutionInput(
                snapshot_price=snapshot.snapshot_price,
                execution_price=snapshot.execution_price_proxy,
                requested_size=snapshot.requested_size,
                snapshot_derived_liquidity=snapshot.snapshot_derived_liquidity,
                observed_possible_fill=snapshot.observed_possible_fill,
                ledger_index_snapshot=snapshot.ledger_index,
                ledger_index_execution=snapshot.ledger_index + 1,
                competition_penalty=snapshot.competition_penalty,
                base_fill_probability=0.85,
                path_complexity=snapshot.path_complexity,
                slippage_estimate=snapshot.slippage_estimate,
            )
        )
        aggregate = self._aggregate_from_tick(snapshot, time_result)
        regime = self.regime_detector.assess(aggregate)
        weighting = self.memory_weighting.evaluate(
            XRPLMemoryWeightingInput(
                global_aggregate=aggregate,
                token_aggregate=aggregate,
                issuer_aggregate=aggregate,
                global_regime=regime,
                token_regime=regime,
                issuer_regime=regime,
            )
        )
        decision = self.trade_gate.evaluate(
            XRPLTradeGateInput(
                requested_size=snapshot.requested_size,
                expected_profit=max(0.0, snapshot.requested_size * 0.05),
                expected_loss=max(0.0, snapshot.requested_size * 0.03),
                threshold=0.0,
                execution_probability_floor=time_result.effective_fill_probability,
                slippage_multiplier=1.0 + snapshot.slippage_estimate,
                liquidity_haircut=1.0 - aggregate.liquidity_reliability,
                phantom_penalty=aggregate.avg_phantom_penalty,
                route_instability=snapshot.route_instability,
                competition_penalty=snapshot.competition_penalty,
                snapshot_price=snapshot.snapshot_price,
                execution_price=snapshot.execution_price_proxy,
                snapshot_derived_liquidity=snapshot.snapshot_derived_liquidity,
                observed_possible_fill=snapshot.observed_possible_fill,
                ledger_index_snapshot=snapshot.ledger_index,
                ledger_index_execution=snapshot.ledger_index + 1,
                path_complexity=snapshot.path_complexity,
                slippage_estimate=snapshot.slippage_estimate,
                memory_probability_multiplier=weighting.execution_probability_multiplier,
                memory_size_multiplier=weighting.effective_size_multiplier,
                memory_slippage_boost=weighting.slippage_multiplier_boost,
                memory_ev_penalty=weighting.ev_penalty,
                memory_risk_flags=weighting.risk_flags,
            )
        )
        return self._record_from_outputs(snapshot, aggregate, regime, weighting, decision, time_result)

    def persist_shadow_decision(self, record: ShadowDecisionRecord) -> ShadowDecisionRecord:
        if not self._is_valid_record(record):
            raise ValueError("invalid shadow decision record")
        with self.session_factory() as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def _is_valid_record(self, record: ShadowDecisionRecord) -> bool:
        if int(record.token_id or 0) <= 0:
            return False
        if not isinstance(record.observed_at, datetime):
            return False
        metrics = [
            _finite_float(record.latency_path_probability),
            _finite_float(record.memory_adjusted_probability),
            _finite_float(record.effective_size),
            _finite_float(record.memory_adjusted_effective_size),
            _finite_float(record.uncertainty_adjusted_value),
            _finite_float(record.drift_adjusted_ev),
        ]
        if any(not isfinite(value) for value in metrics):
            return False
        return any(abs(value) > 0.0 for value in metrics)

    def _aggregate_from_tick(self, snapshot: ShadowSnapshotInput, time_result: XRPLTimeExecutionResult) -> XRPLMemoryAggregate:
        liquidity_decay = (
            0.0
            if snapshot.snapshot_derived_liquidity <= 0.0
            else min(snapshot.observed_possible_fill / max(snapshot.snapshot_derived_liquidity, 1e-9), 1.0)
        )
        phantom_penalty = 0.0
        if snapshot.requested_size > 0.0:
            phantom_penalty = _clamp_unit(
                max(snapshot.snapshot_derived_liquidity - snapshot.observed_possible_fill, 0.0) / snapshot.requested_size
            )
        liquidity_reliability = _clamp_unit(liquidity_decay * (1.0 - phantom_penalty))
        low_fill_bias = _clamp_unit(max(0.0, 0.85 - liquidity_decay))
        execution_reliability = _clamp_unit(
            time_result.effective_fill_probability * (1.0 - low_fill_bias) * (1.0 - snapshot.competition_penalty)
        )
        latency_pressure = _clamp_unit(time_result.latency_seconds / 20.0)
        path_pressure = _clamp_unit(snapshot.path_complexity / 3.0)
        drift_pressure = _clamp_unit(abs(time_result.price_drift) * (1.0 + time_result.latency_seconds / 10.0))
        regime_pressure = _clamp_unit(
            (1.0 - liquidity_reliability) * 0.30
            + (1.0 - execution_reliability) * 0.30
            + snapshot.route_instability * 0.15
            + snapshot.competition_penalty * 0.10
            + max(latency_pressure, path_pressure, drift_pressure) * 0.15
        )
        return XRPLMemoryAggregate(
            scope="shadow_tick",
            key=str(snapshot.token_id),
            sample_count=1,
            avg_phantom_penalty=round(phantom_penalty, 6),
            avg_liquidity_decay=round(liquidity_decay, 6),
            avg_route_instability=round(_clamp_unit(snapshot.route_instability), 6),
            avg_path_complexity=float(max(0, int(snapshot.path_complexity))),
            avg_routes_seen_count=float(max(1, int(snapshot.path_complexity))),
            avg_latency_seconds=time_result.latency_seconds,
            avg_competition_penalty=round(_clamp_unit(snapshot.competition_penalty), 6),
            avg_low_fill_bias=round(low_fill_bias, 6),
            avg_drift=time_result.price_drift,
            avg_drift_adjusted_ev=time_result.drift_adjusted_ev,
            avg_effective_fill_probability=time_result.effective_fill_probability,
            liquidity_reliability=round(liquidity_reliability, 6),
            execution_reliability=round(execution_reliability, 6),
            regime_pressure_score=round(regime_pressure, 6),
            advisory_risk_level=_risk_level(regime_pressure),
        )

    def _record_from_outputs(
        self,
        snapshot: ShadowSnapshotInput,
        aggregate: XRPLMemoryAggregate,
        regime: XRPLRegimeAssessment,
        weighting: XRPLMemoryWeightingResult,
        decision: XRPLTradeGateDecision,
        time_result: XRPLTimeExecutionResult,
    ) -> ShadowDecisionRecord:
        calibration_snapshot = {
            "time_model": {
                "latency_seconds": time_result.latency_seconds,
                "ledger_delay": time_result.ledger_delay,
                "liquidity_decay": time_result.liquidity_decay,
                "drift_amplified": time_result.drift_amplified,
            },
            "memory": aggregate.to_dict(),
            "regime": regime.to_dict(),
            "weighting": weighting.to_dict(),
            "is_advisory": True,
            "is_shadow": True,
            "is_executable": False,
        }
        return ShadowDecisionRecord(
            token_id=int(snapshot.token_id),
            issuer=str(snapshot.issuer),
            currency=str(snapshot.currency),
            observed_at=snapshot.observed_at,
            ledger_index=max(0, int(snapshot.ledger_index)),
            requested_size=round(max(0.0, snapshot.requested_size), 6),
            latency_path_probability=decision.latency_path_adjusted_probability,
            memory_adjusted_probability=decision.memory_adjusted_probability,
            effective_size=decision.effective_size,
            memory_adjusted_effective_size=decision.memory_adjusted_effective_size,
            uncertainty_adjusted_value=decision.uncertainty_adjusted_value,
            drift_adjusted_ev=decision.drift_adjusted_ev,
            regime=regime.regime,
            advisory_risk_level=weighting.advisory_risk_level,
            risk_flags_json=json.dumps(decision.risk_flags, sort_keys=True),
            calibration_snapshot_json=json.dumps(calibration_snapshot, sort_keys=True),
            is_shadow=True,
            is_executable=False,
        )
