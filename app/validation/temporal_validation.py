from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TemporalValidationInput:
    ledger_indices: list[int]
    total_depth_xrp: list[float]
    simulator_latency_ledgers: int


@dataclass(slots=True)
class TemporalValidationResult:
    survivability_half_life: float
    depth_decay_rate: float
    ledger_gap_error: float
    orderbook_collapse_detected: bool
    latency_mismatch_flag: bool


class TemporalValidationLayer:
    def validate(self, data: TemporalValidationInput) -> TemporalValidationResult:
        if not data.ledger_indices or not data.total_depth_xrp or len(data.ledger_indices) != len(data.total_depth_xrp):
            return TemporalValidationResult(
                survivability_half_life=0.0,
                depth_decay_rate=1.0,
                ledger_gap_error=1.0,
                orderbook_collapse_detected=True,
                latency_mismatch_flag=True,
            )

        ordered = sorted(zip(data.ledger_indices, data.total_depth_xrp), key=lambda it: it[0])
        ledgers = [int(it[0]) for it in ordered]
        depths = [max(0.0, float(it[1])) for it in ordered]

        first_depth = max(1e-6, depths[0])
        half_life_ledger = ledgers[-1]
        for lgr, depth in zip(ledgers, depths):
            if depth <= first_depth * 0.50:
                half_life_ledger = lgr
                break
        survivability_half_life = max(0.0, float(half_life_ledger - ledgers[0]))

        decay_losses = []
        collapse_hits = 0
        for prev, curr in zip(depths[:-1], depths[1:]):
            if prev > 0:
                loss = max(0.0, (prev - curr) / prev)
                decay_losses.append(loss)
                if loss >= 0.35:
                    collapse_hits += 1
        depth_decay_rate = 0.0 if not decay_losses else (sum(decay_losses) / len(decay_losses))

        observed_ledger_span = max(0, ledgers[-1] - ledgers[0])
        sim_latency = max(0, int(data.simulator_latency_ledgers))
        ledger_gap_error = abs(sim_latency - observed_ledger_span) / max(1.0, float(max(sim_latency, observed_ledger_span, 1)))

        orderbook_collapse_detected = collapse_hits > 0 or (depths[-1] <= first_depth * 0.35)
        latency_mismatch_flag = ledger_gap_error >= 0.40

        return TemporalValidationResult(
            survivability_half_life=survivability_half_life,
            depth_decay_rate=max(0.0, min(1.0, depth_decay_rate)),
            ledger_gap_error=max(0.0, min(1.0, ledger_gap_error)),
            orderbook_collapse_detected=orderbook_collapse_detected,
            latency_mismatch_flag=latency_mismatch_flag,
        )
