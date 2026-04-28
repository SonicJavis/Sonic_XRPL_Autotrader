from __future__ import annotations

from dataclasses import dataclass

from app.calibration.xrpl_bayesian_calibrator import XRPLShadowCalibrationAggregate


def _clamp_unit(raw: float) -> float:
    return max(0.0, min(1.0, float(raw)))


@dataclass(slots=True)
class XRPLTradeGateInput:
    requested_size: float
    expected_profit: float
    expected_loss: float
    threshold: float
    execution_probability_floor: float
    slippage_multiplier: float
    liquidity_haircut: float
    phantom_penalty: float
    route_instability: float
    competition_penalty: float


@dataclass(slots=True)
class XRPLTradeGateDecision:
    allow_trade: bool
    adjusted_execution_probability: float
    effective_size: float
    uncertainty_adjusted_value: float
    risk_flags: list[str]
    reasoning: str


class XRPLTradeGate:
    """Advisory-only XRPL decision gate under shadow calibration uncertainty."""

    def evaluate_trade(
        self,
        *,
        requested_size: float,
        effective_size: float,
        adjusted_execution_probability: float,
        uncertainty_adjusted_value: float,
        threshold: float,
        slippage_multiplier: float,
        liquidity_haircut: float,
        phantom_penalty: float,
        route_instability: float,
        competition_penalty: float,
    ) -> XRPLTradeGateDecision:
        requested_size = max(0.0, float(requested_size))
        effective_size = max(0.0, float(effective_size))
        adjusted_execution_probability = _clamp_unit(float(adjusted_execution_probability))
        uncertainty_adjusted_value = float(uncertainty_adjusted_value)
        threshold = float(threshold)
        slippage_multiplier = max(1e-9, float(slippage_multiplier))
        liquidity_haircut = _clamp_unit(float(liquidity_haircut))
        phantom_penalty = _clamp_unit(float(phantom_penalty))
        route_instability = _clamp_unit(float(route_instability))
        competition_penalty = _clamp_unit(float(competition_penalty))

        risk_flags: list[str] = []
        if phantom_penalty >= 0.25:
            risk_flags.append("PHANTOM_LIQUIDITY_HIGH")
        if route_instability >= 0.25:
            risk_flags.append("ROUTE_UNSTABLE")
        if competition_penalty >= 0.25:
            risk_flags.append("COMPETITION_RISK_HIGH")
        if adjusted_execution_probability < 0.35:
            risk_flags.append("LOW_EXECUTION_PROBABILITY")
        if slippage_multiplier > 1.25:
            risk_flags.append("HIGH_SLIPPAGE_ENVIRONMENT")
        if effective_size <= 0:
            risk_flags.append("NO_EFFECTIVE_SIZE")
        if liquidity_haircut >= 0.5:
            risk_flags.append("LIQUIDITY_HAIRCUT_HIGH")

        allow_trade = bool(
            effective_size > 0.0
            and adjusted_execution_probability > 0.0
            and uncertainty_adjusted_value > threshold
        )
        reasoning = (
            f"requested_size={requested_size:.6f}; effective_size={effective_size:.6f}; "
            f"adjusted_execution_probability={adjusted_execution_probability:.6f}; "
            f"slippage_multiplier={slippage_multiplier:.6f}; liquidity_haircut={liquidity_haircut:.6f}; "
            f"phantom_penalty={phantom_penalty:.6f}; route_instability={route_instability:.6f}; "
            f"competition_penalty={competition_penalty:.6f}; uncertainty_adjusted_value={uncertainty_adjusted_value:.6f}; "
            f"threshold={threshold:.6f}; allow_trade={allow_trade}"
        )
        return XRPLTradeGateDecision(
            allow_trade=allow_trade,
            adjusted_execution_probability=round(adjusted_execution_probability, 6),
            effective_size=round(effective_size, 6),
            uncertainty_adjusted_value=round(uncertainty_adjusted_value, 6),
            risk_flags=risk_flags,
            reasoning=reasoning,
        )

    def evaluate(self, data: XRPLTradeGateInput) -> XRPLTradeGateDecision:
        requested_size = max(0.0, float(data.requested_size))
        threshold = float(data.threshold)
        expected_profit = float(data.expected_profit)
        expected_loss = max(0.0, float(data.expected_loss))
        execution_probability_floor = _clamp_unit(float(data.execution_probability_floor))
        slippage_multiplier = max(1e-9, float(data.slippage_multiplier))
        liquidity_haircut = _clamp_unit(float(data.liquidity_haircut))
        phantom_penalty = _clamp_unit(float(data.phantom_penalty))
        route_instability = _clamp_unit(float(data.route_instability))
        competition_penalty = _clamp_unit(float(data.competition_penalty))

        effective_size = max(
            0.0,
            requested_size * (1.0 - liquidity_haircut) * (1.0 - phantom_penalty),
        )
        adjusted_execution_probability = _clamp_unit(
            execution_probability_floor * (1.0 - route_instability) * (1.0 - competition_penalty)
        )
        expected_value = (
            adjusted_execution_probability * expected_profit
            - ((1.0 - adjusted_execution_probability) * expected_loss)
        )
        uncertainty_adjusted_value = expected_value / slippage_multiplier

        return self.evaluate_trade(
            requested_size=requested_size,
            effective_size=effective_size,
            adjusted_execution_probability=adjusted_execution_probability,
            uncertainty_adjusted_value=uncertainty_adjusted_value,
            threshold=threshold,
            slippage_multiplier=slippage_multiplier,
            liquidity_haircut=liquidity_haircut,
            phantom_penalty=phantom_penalty,
            route_instability=route_instability,
            competition_penalty=competition_penalty,
        )

    def evaluate_shadow_calibration(
        self,
        *,
        calibration: XRPLShadowCalibrationAggregate,
        requested_size: float,
        expected_profit: float,
        expected_loss: float,
        threshold: float = 0.0,
    ) -> XRPLTradeGateDecision:
        return self.evaluate(
            XRPLTradeGateInput(
                requested_size=requested_size,
                expected_profit=expected_profit,
                expected_loss=expected_loss,
                threshold=threshold,
                execution_probability_floor=calibration.calibration.fill_reliability.lower_bound,
                slippage_multiplier=calibration.calibration.recommendations.expected_slippage_multiplier,
                liquidity_haircut=calibration.calibration.recommendations.liquidity_haircut,
                phantom_penalty=calibration.phantom_penalty_avg,
                route_instability=calibration.route_instability_avg,
                competition_penalty=calibration.competition_failure_rate,
            )
        )