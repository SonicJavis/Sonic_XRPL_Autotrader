import json

from sonic_xrpl.paper_sniper_simulation import load_paper_sniper_batch, run_paper_sniper_simulation
from sonic_xrpl.paper_sniper_simulation.models import FillAssumptionLabel, SimulationDecision
from sonic_xrpl.paper_sniper_simulation.reporting import (
    render_paper_sniper_report_json,
    render_paper_sniper_report_markdown,
)


def _run(path: str):
    batch = load_paper_sniper_batch(path)
    return run_paper_sniper_simulation(batch)


def test_healthy_candidate_is_simulated():
    report = _run("tests/fixtures/paper_sniper_simulation/healthy_candidate_simulated.json")
    row = report.results[0]
    assert row.simulation_decision == SimulationDecision.SIMULATED
    assert row.fill_assumption.label == FillAssumptionLabel.FILLED
    assert row.outcome.assumed_return_bps is not None
    assert row.paper_only is True
    assert row.live_execution_allowed is False


def test_rejected_verdicts_fail_closed():
    for fixture in (
        "tests/fixtures/paper_sniper_simulation/rejected_avoid_verdict.json",
        "tests/fixtures/paper_sniper_simulation/rejected_synthetic_only.json",
        "tests/fixtures/paper_sniper_simulation/rejected_missing_launch_timestamp.json",
        "tests/fixtures/paper_sniper_simulation/rejected_source_conflict.json",
        "tests/fixtures/paper_sniper_simulation/rejected_malformed_record.json",
        "tests/fixtures/paper_sniper_simulation/rejected_missing_liquidity_evidence.json",
        "tests/fixtures/paper_sniper_simulation/rejected_missing_holder_evidence.json",
    ):
        report = _run(fixture)
        row = report.results[0]
        assert row.simulation_decision == SimulationDecision.SIMULATION_REJECTED
        assert row.fill_assumption.label == FillAssumptionLabel.REJECTED
        assert row.outcome.assumed_return_bps is None
        assert row.outcome.assumed_pnl_xrp is None


def test_missing_holder_can_be_rejected_or_limited_by_rule():
    rejected = _run("tests/fixtures/paper_sniper_simulation/rejected_missing_holder_evidence.json").results[0]
    allowed = _run("tests/fixtures/paper_sniper_simulation/allowed_missing_holder_limited.json").results[0]
    assert rejected.simulation_decision == SimulationDecision.SIMULATION_REJECTED
    assert "missing_holder_evidence" in rejected.rejection_reasons
    assert allowed.simulation_decision == SimulationDecision.SIMULATED
    assert "holder_evidence_missing_limited_confidence" in allowed.limitations


def test_no_fill_and_partial_fill_assumptions():
    no_fill = _run("tests/fixtures/paper_sniper_simulation/thin_liquidity_no_fill.json").results[0]
    partial = _run("tests/fixtures/paper_sniper_simulation/thin_liquidity_partial_fill.json").results[0]
    assert no_fill.fill_assumption.label == FillAssumptionLabel.NO_FILL
    assert no_fill.outcome.assumed_return_bps is None
    assert partial.fill_assumption.label == FillAssumptionLabel.PARTIAL_FILL
    assert 0 < partial.fill_assumption.fill_ratio < 1


def test_high_slippage_assumption_is_marked():
    row = _run("tests/fixtures/paper_sniper_simulation/high_slippage_assumption.json").results[0]
    assert "high_slippage_assumption" in row.risk_notes


def test_stale_watch_can_simulate_when_explicitly_allowed():
    row = _run("tests/fixtures/paper_sniper_simulation/stale_reduced_confidence.json").results[0]
    assert row.simulation_decision == SimulationDecision.SIMULATED
    assert "stale_evidence" in row.risk_notes


def test_same_symbol_different_issuer_stays_separate():
    rows = _run("tests/fixtures/paper_sniper_simulation/same_symbol_different_issuer.json").results
    assert len(rows) == 2
    assert rows[0].candidate_id != rows[1].candidate_id
    assert rows[0].issuer != rows[1].issuer


def test_reporting_outputs_are_non_executing():
    report = _run("tests/fixtures/paper_sniper_simulation/healthy_candidate_simulated.json")
    payload = render_paper_sniper_report_json(report)
    markdown = render_paper_sniper_report_markdown(report)
    assert '"live_execution_allowed": false' in payload
    assert "Paper-only simulation output" in markdown


def test_loader_omitted_liquidity_uses_default(tmp_path):
    fixture = tmp_path / "omitted_liquidity.json"
    fixture.write_text(
        json.dumps(
            {
                "intelligence_fixture": "tests/fixtures/firstledger_intelligence/source_backed_healthy.json",
                "simulations": [
                    {
                        "candidate_id": "phase59_source_backed_healthy",
                        "entry_price_xrp": 0.5,
                        "exit_price_xrp": 0.6,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    batch = load_paper_sniper_batch(fixture)
    assert batch.scenarios[0].liquidity_available_pct_assumption == 1.0
    report = run_paper_sniper_simulation(batch)
    row = report.results[0]
    assert row.fill_assumption.label == FillAssumptionLabel.FILLED
    assert "missing_liquidity_assumption" not in row.limitations


def test_loader_explicit_null_liquidity_remains_missing(tmp_path):
    fixture = tmp_path / "null_liquidity.json"
    fixture.write_text(
        json.dumps(
            {
                "intelligence_fixture": "tests/fixtures/firstledger_intelligence/source_backed_healthy.json",
                "simulations": [
                    {
                        "candidate_id": "phase59_source_backed_healthy",
                        "entry_price_xrp": 0.5,
                        "exit_price_xrp": 0.6,
                        "liquidity_available_pct_assumption": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    batch = load_paper_sniper_batch(fixture)
    assert batch.scenarios[0].liquidity_available_pct_assumption is None
    report = run_paper_sniper_simulation(batch)
    row = report.results[0]
    assert row.fill_assumption.label == FillAssumptionLabel.NO_FILL
    assert row.fill_assumption.no_fill_reason == "missing_liquidity_assumption"
