from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DriftRegimeMonitorResult:
    alert_level: str
    regime_transition_rate: float
    instability_score: float
    worsening_drift_rate: float


class DriftRegimeMonitor:
    def assess(self, *, drift_errors: list[float], regimes: list[str]) -> DriftRegimeMonitorResult:
        normalized_drift = [max(0.0, min(1.0, float(v))) for v in drift_errors]

        worsening_steps = 0
        for prev, curr in zip(normalized_drift[:-1], normalized_drift[1:]):
            if curr > prev:
                worsening_steps += 1
        drift_steps = max(1, len(normalized_drift) - 1)
        worsening_drift_rate = worsening_steps / drift_steps

        transitions = 0
        for prev, curr in zip(regimes[:-1], regimes[1:]):
            if prev != curr:
                transitions += 1
        regime_steps = max(1, len(regimes) - 1)
        regime_transition_rate = transitions / regime_steps

        avg_drift = 0.0 if not normalized_drift else sum(normalized_drift) / len(normalized_drift)
        instability_score = max(
            0.0,
            min(
                1.0,
                (avg_drift * 0.45)
                + (worsening_drift_rate * 0.30)
                + (regime_transition_rate * 0.25),
            ),
        )

        alert_level = "LOW"
        if instability_score >= 0.75:
            alert_level = "HIGH"
        if worsening_drift_rate >= 0.5 and regime_transition_rate >= 0.4:
            alert_level = "CRITICAL"
        elif instability_score >= 0.9:
            alert_level = "CRITICAL"
        elif instability_score >= 0.55 and alert_level != "CRITICAL":
            alert_level = "MEDIUM"

        return DriftRegimeMonitorResult(
            alert_level=alert_level,
            regime_transition_rate=regime_transition_rate,
            instability_score=instability_score,
            worsening_drift_rate=worsening_drift_rate,
        )
