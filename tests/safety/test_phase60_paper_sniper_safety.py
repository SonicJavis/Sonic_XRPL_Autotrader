from pathlib import Path

from sonic_xrpl.paper_sniper_simulation import load_paper_sniper_batch, run_paper_sniper_simulation
from sonic_xrpl.paper_sniper_simulation.models import SimulationDecision


def _run(path: str):
    return run_paper_sniper_simulation(load_paper_sniper_batch(path))


def test_phase60_layer_has_no_live_execution_keywords():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/paper_sniper_simulation").glob("*.py"))
    forbidden = [
        "submitAndWait",
        "autofill",
        "fromSeed",
        "familySeed",
        "Wallet(",
        "Xaman",
        "Xumm",
        "OfferCreate",
        "Payment",
        "TrustSet",
        "requests.get(",
        "wss://",
        "https://",
    ]
    for token in forbidden:
        assert token not in combined


def test_phase60_rejected_categories_do_not_simulate_entry():
    for fixture in (
        "tests/fixtures/paper_sniper_simulation/rejected_avoid_verdict.json",
        "tests/fixtures/paper_sniper_simulation/rejected_synthetic_only.json",
        "tests/fixtures/paper_sniper_simulation/rejected_source_conflict.json",
        "tests/fixtures/paper_sniper_simulation/rejected_missing_launch_timestamp.json",
        "tests/fixtures/paper_sniper_simulation/rejected_missing_holder_evidence.json",
    ):
        row = _run(fixture).results[0]
        assert row.simulation_decision == SimulationDecision.SIMULATION_REJECTED


def test_phase60_outputs_are_paper_only_and_not_real_pnl():
    row = _run("tests/fixtures/paper_sniper_simulation/healthy_candidate_simulated.json").results[0]
    assert row.paper_only is True
    assert row.review_only is True
    assert row.live_execution_allowed is False
    assert row.transaction_created is False
    assert row.order_created is False
    assert row.outcome.real_pnl is False
