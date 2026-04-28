from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DualErrorInput:
    simulator_fillable: bool
    simulator_fill_ratio: float
    observed_depth_present: bool
    observation_confidence: float
    observed_fill_probability: float


@dataclass(slots=True)
class DualErrorResult:
    simulator_error: float
    observation_error: float
    disagreement_score: float
    confidence_weighted_error: float
    false_confidence_flag: bool
    simulator_uncertain: bool
    observation_uncertain: bool


class DualErrorEngine:
    def evaluate(self, data: DualErrorInput) -> DualErrorResult:
        sim_fill_ratio = max(0.0, min(1.0, float(data.simulator_fill_ratio)))
        obs_fill_prob = max(0.0, min(1.0, float(data.observed_fill_probability)))
        obs_conf = max(0.0, min(1.0, float(data.observation_confidence)))

        simulator_uncertain = sim_fill_ratio <= 0.15
        observation_uncertain = (not bool(data.observed_depth_present)) or (obs_conf < 0.45)

        simulator_signal = 1.0 if bool(data.simulator_fillable) else 0.0
        observation_signal = 1.0 if bool(data.observed_depth_present) else 0.0

        base_disagreement = abs(simulator_signal - observation_signal)
        probabilistic_disagreement = abs(sim_fill_ratio - obs_fill_prob)
        disagreement_score = max(0.0, min(1.0, (base_disagreement * 0.55) + (probabilistic_disagreement * 0.45)))

        simulator_error = max(0.0, min(1.0, abs(sim_fill_ratio - obs_fill_prob) * obs_conf))
        observation_error = max(0.0, min(1.0, ((1.0 - obs_conf) * 0.65) + (base_disagreement * 0.35)))

        both_uncertain = simulator_uncertain and observation_uncertain
        if both_uncertain:
            disagreement_score = max(0.0, min(1.0, disagreement_score * 0.35))
            simulator_error = max(0.0, min(1.0, simulator_error * 0.40))
            observation_error = max(0.0, min(1.0, observation_error * 0.50))

        confidence_weighted_error = max(
            0.0,
            min(
                1.0,
                ((simulator_error * 0.50) + (observation_error * 0.50)) * max(0.10, obs_conf),
            ),
        )

        false_confidence_flag = False
        if disagreement_score >= 0.55 and obs_conf >= 0.65 and not both_uncertain:
            false_confidence_flag = True

        # Low-confidence observations cannot be used to claim simulator is wrong.
        if obs_conf < 0.45:
            false_confidence_flag = False

        return DualErrorResult(
            simulator_error=simulator_error,
            observation_error=observation_error,
            disagreement_score=disagreement_score,
            confidence_weighted_error=confidence_weighted_error,
            false_confidence_flag=false_confidence_flag,
            simulator_uncertain=simulator_uncertain,
            observation_uncertain=observation_uncertain,
        )
