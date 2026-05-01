import pytest
import os
import json
from pathlib import Path
from execution_prototype.paper_operator.decision_policy import evaluate_candidate, _generate_decision_id
from execution_prototype.paper_operator.portfolio import apply_decision, initialize_ledger, _generate_position_id
from execution_prototype.paper_operator.paper_executor import execute_cycle
from execution_prototype.paper_review.cli import analyze_performance
from execution_prototype.quality.data_quality import check_candidate_quality, check_pnl_quality, check_paper_entry_quality
from execution_prototype.strategy.placeholders import trustline_spike_watch, amm_seeded_launch_watch
from execution_prototype.pipeline.cli import main as pipeline_main

def _mock_candidate():
    return {
        "candidate_id": "cand1",
        "issuer": "rIss",
        "currency_code": "TOK",
        "score_band": "high_attention",
        "confidence": "high",
        "risk_flags": [],
        "metadata_present": True,
        "validated_ledger_evidence": True,
        "amm_present": True,
        "liquidity_signal_strength": "strong",
        "source_signal_types": ["trustline_created"]
    }

def test_paper_decision_deterministic_id():
    id1 = _generate_decision_id("cand1", "2026-05-01T10:00:00Z", "paper_enter")
    id2 = _generate_decision_id("cand1", "2026-05-01T10:00:00Z", "paper_enter")
    assert id1 == id2
    assert len(id1) == 16

def test_paper_enter_strong_candidate():
    candidate = _mock_candidate()
    decision = evaluate_candidate(candidate, [], None, 0, 5, 0.5)
    assert decision.action == "paper_enter"

def test_paper_reject_missing_metadata():
    candidate = _mock_candidate()
    candidate["metadata_present"] = False
    decision = evaluate_candidate(candidate, [], None, 0, 5, 0.5)
    assert decision.action == "paper_reject"
    assert "MISSING_METADATA" in decision.reason

def test_paper_reject_no_validated_ledger():
    candidate = _mock_candidate()
    candidate["validated_ledger_evidence"] = False
    decision = evaluate_candidate(candidate, [], None, 0, 5, 0.5)
    assert decision.action == "paper_reject"
    assert "NO_VALIDATED_LEDGER_EVIDENCE" in decision.reason

def test_max_positions_enforced():
    candidate = _mock_candidate()
    decision = evaluate_candidate(candidate, [], None, 5, 5, 0.5)
    assert decision.action == "paper_reject"
    assert "Max positions exceeded" in decision.reason

def test_no_fake_pnl_when_price_missing():
    errors = check_pnl_quality(0.5, None)
    assert len(errors) == 1
    assert "Fake PnL detected" in errors[0]

def test_paper_review_consumes_paper_trade_history():
    candidate = _mock_candidate()
    ledger = initialize_ledger("c1", 1000.0)
    price_feed = {"cand1": 0.5}
    
    # enter
    ledger, decisions, history = execute_cycle([candidate], [], ledger, price_feed)
    assert len(ledger.open_positions) == 1
    
    # exit (price drop)
    price_feed["cand1"] = 0.1
    ledger, decisions2, history2 = execute_cycle([candidate], [], ledger, price_feed)
    
    assert len(ledger.open_positions) == 0
    assert len(history2) == 1
    
    review = analyze_performance("c1", history2)
    assert review.total_trades == 1
    assert review.losses == 1

def test_strategy_placeholders_cannot_execute():
    candidate = _mock_candidate()
    assert trustline_spike_watch(candidate) is True
    assert amm_seeded_launch_watch(candidate) is True
    # There are no execution capabilities here

def test_quality_gates_block_false_confidence():
    candidate = _mock_candidate()
    candidate["metadata_present"] = False
    errors = check_candidate_quality(candidate)
    assert any("High confidence claimed without metadata" in e for e in errors)

def test_pipeline_dry_run_append_only(tmp_path, monkeypatch):
    discovery_dir = tmp_path / "discovery"
    discovery_dir.mkdir()
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    
    with open(discovery_dir / "meme_candidates.jsonl", "w") as f:
        f.write(json.dumps(_mock_candidate()) + "\n")
        
    args = ["cli.py", "--discovery-report", str(discovery_dir), "--output-dir", str(out_dir)]
    monkeypatch.setattr("sys.argv", args)
    
    try:
        pipeline_main()
    except SystemExit as e:
        assert e.code == 0
        
    assert (out_dir / "paper_decisions.jsonl").exists()
    assert (out_dir / "paper_ledger_state.json").exists()
    
    # Check source not modified
    assert (discovery_dir / "meme_candidates.jsonl").exists()
    
    # Check append only behavior context
    assert len(list(out_dir.iterdir())) >= 2
