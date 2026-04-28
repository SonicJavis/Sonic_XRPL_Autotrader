from __future__ import annotations

from math import ceil

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.decision.xrpl_trade_gate import XRPLTradeGate, XRPLTradeGateInput

router = APIRouter()


def _clamp_unit(raw: float) -> float:
    return max(0.0, min(1.0, float(raw)))


class TradeGateFillReliabilityInput(BaseModel):
    lower_bound: float = Field(ge=0.0, le=1.0)


class TradeGateCalibrationInput(BaseModel):
    fill_reliability: TradeGateFillReliabilityInput
    expected_slippage_multiplier: float = Field(gt=0.0)
    liquidity_haircut: float = Field(ge=0.0, le=1.0)
    phantom_penalty: float = Field(ge=0.0, le=1.0)
    route_instability: float = Field(ge=0.0, le=1.0)
    competition_penalty: float = Field(ge=0.0, le=1.0)
    ledger_delay_error: float = Field(ge=0.0, le=1.0)
    snapshot_price: float = Field(default=1.0, ge=0.0)
    execution_price: float = Field(default=1.0, ge=0.0)
    snapshot_derived_liquidity: float = Field(default=1.0, ge=0.0)
    observed_possible_fill: float = Field(default=1.0, ge=0.0)
    path_complexity: int = Field(default=0, ge=0)
    slippage_estimate: float = Field(default=0.0, ge=0.0)


class TradeGateEvaluateRequest(BaseModel):
    requested_size: float = Field(ge=0.0)
    expected_profit: float
    expected_loss: float = Field(ge=0.0)
    calibration: TradeGateCalibrationInput


@router.post("/trade-gate/evaluate")
def trade_gate_evaluate(payload: TradeGateEvaluateRequest) -> dict[str, object]:
    requested_size = max(0.0, float(payload.requested_size))
    calibration = payload.calibration
    ledger_delay = ceil(float(calibration.ledger_delay_error) * 3.0)
    path_complexity = int(calibration.path_complexity or ceil(float(calibration.route_instability) * 3.0))
    adjusted_slippage = max(
        1e-9,
        float(calibration.expected_slippage_multiplier)
        * (1.0 + float(calibration.route_instability))
        * (1.0 + float(calibration.competition_penalty)),
    )
    decision = XRPLTradeGate().evaluate(
        data=XRPLTradeGateInput(
            requested_size=requested_size,
            expected_profit=float(payload.expected_profit),
            expected_loss=float(payload.expected_loss),
            threshold=0.0,
            execution_probability_floor=_clamp_unit(float(calibration.fill_reliability.lower_bound)),
            slippage_multiplier=adjusted_slippage,
            liquidity_haircut=float(calibration.liquidity_haircut),
            phantom_penalty=float(calibration.phantom_penalty),
            route_instability=float(calibration.route_instability),
            competition_penalty=float(calibration.competition_penalty),
            snapshot_price=float(calibration.snapshot_price),
            execution_price=float(calibration.execution_price),
            snapshot_derived_liquidity=float(calibration.snapshot_derived_liquidity),
            observed_possible_fill=float(calibration.observed_possible_fill),
            ledger_index_snapshot=0,
            ledger_index_execution=ledger_delay,
            path_complexity=path_complexity,
            slippage_estimate=float(calibration.slippage_estimate),
        )
    )
    return {
        "allow_trade": decision.allow_trade,
        "effective_size": decision.effective_size,
        "latency_path_adjusted_probability": decision.latency_path_adjusted_probability,
        "uncertainty_adjusted_value": decision.uncertainty_adjusted_value,
        "drift_adjusted_ev": decision.drift_adjusted_ev,
        "risk_flags": decision.risk_flags,
        "reasoning": decision.reasoning,
        "is_advisory": True,
        "is_executable": False,
        "is_shadow": True,
        "xrpl_warning": "Orderbook is snapshot-based and not guaranteed executable",
    }
