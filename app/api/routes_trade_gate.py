from __future__ import annotations

from math import exp

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.decision.xrpl_trade_gate import XRPLTradeGate

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


class TradeGateEvaluateRequest(BaseModel):
    requested_size: float = Field(ge=0.0)
    expected_profit: float
    expected_loss: float = Field(ge=0.0)
    calibration: TradeGateCalibrationInput


@router.post("/trade-gate/evaluate")
def trade_gate_evaluate(payload: TradeGateEvaluateRequest) -> dict[str, object]:
    requested_size = max(0.0, float(payload.requested_size))
    calibration = payload.calibration
    fill_prob = _clamp_unit(
        float(calibration.fill_reliability.lower_bound)
        * (1.0 - float(calibration.route_instability))
        * (1.0 - float(calibration.competition_penalty))
        * exp(-float(calibration.ledger_delay_error))
    )
    effective_size = max(
        0.0,
        requested_size
        * (1.0 - float(calibration.liquidity_haircut))
        * (1.0 - float(calibration.phantom_penalty))
        * fill_prob,
    )
    adjusted_slippage = max(
        1e-9,
        float(calibration.expected_slippage_multiplier)
        * (1.0 + float(calibration.route_instability))
        * (1.0 + float(calibration.competition_penalty)),
    )
    adjusted_ev = (
        fill_prob * float(payload.expected_profit)
        - ((1.0 - fill_prob) * float(payload.expected_loss))
        - (adjusted_slippage * requested_size * 0.01)
    )

    decision = XRPLTradeGate().evaluate_trade(
        requested_size=requested_size,
        effective_size=effective_size,
        adjusted_execution_probability=fill_prob,
        uncertainty_adjusted_value=adjusted_ev,
        threshold=0.0,
        slippage_multiplier=adjusted_slippage,
        liquidity_haircut=float(calibration.liquidity_haircut),
        phantom_penalty=float(calibration.phantom_penalty),
        route_instability=float(calibration.route_instability),
        competition_penalty=float(calibration.competition_penalty),
    )
    return {
        "allow_trade": decision.allow_trade,
        "effective_size": decision.effective_size,
        "adjusted_execution_probability": decision.adjusted_execution_probability,
        "uncertainty_adjusted_value": decision.uncertainty_adjusted_value,
        "risk_flags": decision.risk_flags,
        "reasoning": decision.reasoning,
        "is_advisory": True,
        "is_executable": False,
        "is_shadow": True,
        "xrpl_warning": "Orderbook is snapshot-based and not guaranteed executable",
    }