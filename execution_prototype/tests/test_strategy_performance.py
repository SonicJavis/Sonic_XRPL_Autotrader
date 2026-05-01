import pytest
import json
from pathlib import Path
from execution_prototype.strategy_performance.models import StrategyEvaluation, StrategyBacktestResult, StrategyTournamentResult
from execution_prototype.strategy_performance.strategy_runner import _generate_evaluation_id, trustline_spike_watch, STRATEGY_REGISTRY
from execution_prototype.strategy_performance.backtest_engine import _generate_backtest_id, evaluate_strategy_on_candidates, backtest_strategy
from execution_prototype.strategy_performance.tournament import _generate_tournament_id, run_tournament
from execution_prototype.strategy_performance.cli import main as cli_main

def _mock_candidates():
    return [
        {
            "candidate_id": "cand_1",
            "issuer": "iss1",
            "currency_code": "TOK",
            "score_band": "high_attention",
            "confidence": "high",
            "metadata_present": True,
            "amm_present": True,
            "source_signal_types": ["trustline_created", "MPT_ISSUANCE"],
            "risk_flags": []
        },
        {
            "candidate_id": "cand_2", # same ticker different issuer
            "issuer": "iss2",
            "currency_code": "TOK",
            "score_band": "review",
            "metadata_present": False,
            "amm_present": False,
            "source_signal_types": ["OfferCreate", "offer_activity_low_confidence"],
            "risk_flags": []
        }
    ]

def _mock_trades():
    return [
        {
            "candidate_id": "cand_1",
            "outcome": "win",
            "paper_pnl_pct": 20.5
        }
        # cand_2 is missing a price/trade -> unknown
    ]

def test_deterministic_ids():
    e1 = _generate_evaluation_id("s1", "c1")
    e2 = _generate_evaluation_id("s1", "c1")
    assert e1 == e2

    b1 = _generate_backtest_id("s1")
    b2 = _generate_backtest_id("s1")
    assert b1 == b2

def test_missing_trade_produces_unknown_outcome():
    evals = evaluate_strategy_on_candidates("aggressive_high_attention_paper_only", _mock_candidates())
    bt = backtest_strategy("aggressive_high_attention_paper_only", evals, _mock_trades(), _mock_candidates())
    
    # cand_2 is high_attention? No, it's "review", so it won't be entered by aggressive.
    # cand_1 is high_attention, so it will be entered.
    assert bt.paper_wins == 1
    
    # let's evaluate all candidates using a strategy that enters everything like trustline
    evals2 = evaluate_strategy_on_candidates("trustline_spike_watch", _mock_candidates())
    # Wait, cand_2 has no trustline_created. It won't be entered.
    
    # Create a custom evaluation that enters everything
    eval_all = [
        StrategyEvaluation("e1", "test", "cand_1", True, False, False, False, "", [], [], "high", [], ""),
        StrategyEvaluation("e2", "test", "cand_2", True, False, False, False, "", [], [], "low", [], "")
    ]
    bt2 = backtest_strategy("test", eval_all, _mock_trades(), _mock_candidates())
    assert bt2.unknown_outcomes == 1 # cand_2
    assert bt2.unknown_outcome_rate == 50.0

def test_metadata_backed_strategy_confidence():
    evals = evaluate_strategy_on_candidates("metadata_backed_high_attention", _mock_candidates())
    assert evals[0].confidence == "high" # metadata present
    assert evals[1].confidence == "low"  # missing metadata

def test_tournament_never_authorizes_live_trading():
    bt1 = StrategyBacktestResult("b1", "s1", 2, 1, 0, 1, 0, 0, 0, 100.0, 0.0, 0.0, 20.0, 0.0, 0.0, 0.0, 0, 0, 100.0, 0.0, 100.0, 100.0, [], 80.0, "high", [], "")
    tourney = run_tournament([bt1])
    assert tourney.human_review_required is True
    assert "Live trading" in tourney.prohibited_auto_action

def test_protocol_features_annotated_not_invented():
    evals = evaluate_strategy_on_candidates("mpt_feature_watch", _mock_candidates())
    assert "MPT" in evals[0].protocol_feature_context
    assert "MPT" not in evals[1].protocol_feature_context

def test_cli_dry_run(tmp_path, monkeypatch):
    disc_dir = tmp_path / "discovery"
    paper_dir = tmp_path / "paper"
    out_dir = tmp_path / "out"
    
    disc_dir.mkdir()
    paper_dir.mkdir()
    
    with open(disc_dir / "meme_candidates.jsonl", "w") as f:
        for c in _mock_candidates():
            f.write(json.dumps(c) + "\n")
            
    with open(paper_dir / "paper_trade_history.jsonl", "w") as f:
        for t in _mock_trades():
            f.write(json.dumps(t) + "\n")
            
    args = ["cli.py", "--discovery-report", str(disc_dir), "--paper-report", str(paper_dir), "--output-dir", str(out_dir), "--dry-run"]
    monkeypatch.setattr("sys.argv", args)
    
    try:
        cli_main()
    except SystemExit as e:
        assert e.code == 0
        
    assert not out_dir.exists() # Dry run didn't write
