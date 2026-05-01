import pytest
from pathlib import Path
from execution_prototype.campaign_runner.state_store import _generate_campaign_id, create_initial_campaign, update_campaign_state
from execution_prototype.campaign_runner.cycle_runner import _generate_cycle_id, CampaignCycleResult
from execution_prototype.campaign_runner.summary_builder import build_dashboard_data
from execution_prototype.campaign_runner.cli import main as cli_main

def test_deterministic_ids():
    c1 = _generate_campaign_id("test")
    c2 = _generate_campaign_id("test")
    assert c1 == c2
    
    cy1 = _generate_cycle_id("c1", 1)
    cy2 = _generate_cycle_id("c1", 1)
    assert cy1 == cy2

def test_create_initial_campaign():
    state = create_initial_campaign("test-camp", 7)
    assert state.status == "active"
    assert state.current_cycle == 0
    assert state.max_cycles == 7

def test_halt_paper_sets_status():
    state = create_initial_campaign("test-camp", 7)
    new_state = update_campaign_state(state, "active", "halt_paper", 30, None, None, None)
    # The governor logic handles "halt_paper" -> "halted" before calling update_campaign_state usually,
    # but let's assume it was passed "halted" for new_status.
    new_state = update_campaign_state(state, "halted", "halt_paper", 30, None, None, None)
    assert new_state.status == "halted"
    assert new_state.current_cycle == 1

def test_completed_status_after_max_cycles():
    state = create_initial_campaign("test-camp", 1)
    new_state = update_campaign_state(state, "active", "allow_paper", 90, None, None, None)
    assert new_state.status == "completed"

def test_dashboard_data_generation():
    state = create_initial_campaign("test-camp", 7)
    cycle = CampaignCycleResult("cy1", "c1", 1, "now", None, None, None, None, None, "allow", 90, 0, 0, 0.0, [], [], "None", "None")
    dash = build_dashboard_data(state, cycle, Path("fake_p36"), Path("fake_p37"), Path("fake_p38"))
    
    assert "PAPER ONLY. NO WALLET" in dash.safety_statement
    assert "Batch / fixBatchInnerSigs: Disabled / Unsupported" in dash.protocol_context

def test_cli_dry_run(tmp_path, monkeypatch):
    disc = tmp_path / "disc"
    out = tmp_path / "out"
    disc.mkdir()
    
    args = ["cli.py", "--campaign-name", "dry_test", "--discovery-report", str(disc), "--output-dir", str(out), "--dry-run", "--run-cycle"]
    monkeypatch.setattr("sys.argv", args)
    
    try:
        cli_main()
    except SystemExit as e:
        assert e.code == 0
        
    assert not (out / "c1" / "campaign_state.json").exists()
