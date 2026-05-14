from __future__ import annotations

from sonic_xrpl.paper_sniper_simulation.models import (
    FillAssumptionLabel,
    PaperOutcomeSummary,
    PaperSniperBatch,
    PaperSniperSimulationReport,
    PaperSniperSimulationResult,
    SimulationDecision,
)
from sonic_xrpl.paper_sniper_simulation.rules import build_fill_assumption, rejection_reasons


_GENERATED_AT = "1970-01-01T00:00:00+00:00"


def _assumed_return_bps(entry: float | None, exit_price: float | None, slippage_bps: int) -> float | None:
    if entry is None or exit_price is None or entry <= 0:
        return None
    raw = ((exit_price - entry) / entry) * 10000.0
    return round(raw - float(max(0, slippage_bps)), 4)


def _assumed_pnl_xrp(entry: float | None, exit_price: float | None, fill_ratio: float) -> float | None:
    if entry is None or exit_price is None:
        return None
    return round((exit_price - entry) * fill_ratio, 8)


def run_paper_sniper_simulation(batch: PaperSniperBatch) -> PaperSniperSimulationReport:
    scenario_by_id = {row.candidate_id: row for row in batch.scenarios}
    rows: list[PaperSniperSimulationResult] = []

    for item in sorted(batch.intelligence_results, key=lambda row: row.candidate_id):
        scenario = scenario_by_id.get(item.candidate_id)
        if scenario is None:
            from sonic_xrpl.paper_sniper_simulation.models import PaperSniperScenario

            scenario = PaperSniperScenario(candidate_id=item.candidate_id)
        rejected_reasons = rejection_reasons(item, scenario)
        rejected = bool(rejected_reasons)

        fill = build_fill_assumption(item, scenario, rejected)
        decision = SimulationDecision.SIMULATION_REJECTED if rejected else SimulationDecision.SIMULATED

        assumed_return = _assumed_return_bps(
            scenario.entry_price_xrp,
            scenario.exit_price_xrp,
            fill.slippage_bps_assumption,
        )
        assumed_pnl = _assumed_pnl_xrp(
            scenario.entry_price_xrp,
            scenario.exit_price_xrp,
            fill.fill_ratio,
        )
        if fill.label in {FillAssumptionLabel.NO_FILL, FillAssumptionLabel.REJECTED}:
            assumed_return = None
            assumed_pnl = None

        risk_notes = [
            f"intelligence_verdict={item.verdict.value}",
            f"confidence={item.confidence.score}/{item.confidence.band}",
        ]
        if item.launch_evidence.stale:
            risk_notes.append("stale_evidence")
        if fill.slippage_bps_assumption >= 400:
            risk_notes.append("high_slippage_assumption")

        provenance_notes = [
            f"source_type={item.source_provenance.source_type}",
            f"source_backed={item.source_provenance.source_backed}",
            f"synthetic={item.source_provenance.synthetic}",
        ]

        limitations = list(item.limitations)
        if scenario.notes:
            limitations.extend(scenario.notes)
        if fill.label == FillAssumptionLabel.NO_FILL and fill.no_fill_reason:
            limitations.append(fill.no_fill_reason)
        if fill.label == FillAssumptionLabel.PARTIAL_FILL and fill.partial_fill_reason:
            limitations.append(fill.partial_fill_reason)

        rows.append(
            PaperSniperSimulationResult(
                candidate_id=item.candidate_id,
                issuer=item.issuer,
                symbol=item.symbol,
                intelligence_verdict=item.verdict.value,
                simulation_decision=decision,
                fill_assumption=fill,
                outcome=PaperOutcomeSummary(
                    outcome_window=scenario.outcome_window,
                    assumed_entry_price_xrp=scenario.entry_price_xrp,
                    assumed_exit_price_xrp=scenario.exit_price_xrp,
                    assumed_return_bps=assumed_return,
                    assumed_pnl_xrp=assumed_pnl,
                    outcome_is_assumption=True,
                    real_pnl=False,
                ),
                rejection_reasons=rejected_reasons,
                risk_notes=tuple(dict.fromkeys(risk_notes)),
                provenance_notes=tuple(dict.fromkeys(provenance_notes)),
                limitations=tuple(dict.fromkeys(limitations)),
                paper_only=True,
                review_only=True,
                live_execution_allowed=False,
                transaction_created=False,
                order_created=False,
            )
        )

    by_decision: dict[str, int] = {}
    simulated = 0
    rejected = 0
    no_fill = 0
    partial_fill = 0
    for row in rows:
        by_decision[row.simulation_decision.value] = by_decision.get(row.simulation_decision.value, 0) + 1
        if row.simulation_decision == SimulationDecision.SIMULATED:
            simulated += 1
        else:
            rejected += 1
        if row.fill_assumption.label == FillAssumptionLabel.NO_FILL:
            no_fill += 1
        if row.fill_assumption.label == FillAssumptionLabel.PARTIAL_FILL:
            partial_fill += 1

    return PaperSniperSimulationReport(
        report_id=f"phase60_{len(rows)}_candidates",
        generated_at=_GENERATED_AT,
        total_candidates=len(rows),
        simulated_candidates=simulated,
        rejected_candidates=rejected,
        no_fill_candidates=no_fill,
        partial_fill_candidates=partial_fill,
        by_decision=by_decision,
        results=tuple(rows),
        paper_only=True,
        review_only=True,
        live_execution_allowed=False,
    )
