from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ExecutionBoundsInput:
    total_visible_depth_xrp: float
    requested_size_xrp: float
    depth_uncertainty: float
    fundedness_uncertainty: float
    decay_rate: float
    regime: str = "UNKNOWN"


@dataclass(slots=True)
class ExecutionBoundsResult:
    min_executable_size: float
    max_possible_fill: float
    fill_probability_range: tuple[float, float]
    confidence: float
    simulator_within_bounds: bool


class ExecutionBoundsModel:
    def compute(self, *, data: ExecutionBoundsInput, simulator_fill_size_xrp: float) -> ExecutionBoundsResult:
        requested = max(0.0, float(data.requested_size_xrp))
        visible_depth = max(0.0, float(data.total_visible_depth_xrp))
        depth_uncertainty = max(0.0, min(1.0, float(data.depth_uncertainty)))
        fundedness_uncertainty = max(0.0, min(1.0, float(data.fundedness_uncertainty)))
        decay = max(0.0, min(1.0, float(data.decay_rate)))

        if requested <= 0:
            return ExecutionBoundsResult(
                min_executable_size=0.0,
                max_possible_fill=0.0,
                fill_probability_range=(0.0, 0.0),
                confidence=0.01,
                simulator_within_bounds=True,
            )

        depth_ratio = max(0.0, min(1.0, visible_depth / requested))
        combined_uncertainty = max(
            0.0,
            min(
                1.0,
                (depth_uncertainty * 0.45)
                + (fundedness_uncertainty * 0.35)
                + (decay * 0.20),
            ),
        )

        regime_uncertainty_boost = 0.0
        if data.regime == "SPOOFY":
            regime_uncertainty_boost = 0.25
        elif data.regime == "THIN":
            regime_uncertainty_boost = 0.15
        elif data.regime == "STABLE":
            regime_uncertainty_boost = -0.08
        combined_uncertainty = max(0.0, min(1.0, combined_uncertainty + regime_uncertainty_boost))

        optimistic_fill_ratio = max(0.0, min(1.0, depth_ratio * (1.0 - (combined_uncertainty * 0.35))))
        conservative_fill_ratio = max(0.0, min(optimistic_fill_ratio, optimistic_fill_ratio * (1.0 - combined_uncertainty)))

        max_possible_fill = requested * optimistic_fill_ratio
        min_executable_size = requested * conservative_fill_ratio

        min_prob = max(0.0, min(1.0, conservative_fill_ratio * (1.0 - combined_uncertainty * 0.50)))
        max_prob = max(min_prob, min(1.0, optimistic_fill_ratio))

        confidence = max(0.01, min(1.0, 1.0 - combined_uncertainty))

        sim_fill = max(0.0, float(simulator_fill_size_xrp))
        simulator_within_bounds = (sim_fill >= (min_executable_size - 1e-6)) and (sim_fill <= (max_possible_fill + 1e-6))

        return ExecutionBoundsResult(
            min_executable_size=min_executable_size,
            max_possible_fill=max_possible_fill,
            fill_probability_range=(min_prob, max_prob),
            confidence=confidence,
            simulator_within_bounds=simulator_within_bounds,
        )
