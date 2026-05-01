import pytest
from execution_prototype.risk_governor.trust_score import _generate_trust_score_id, calculate_trust_score
from execution_prototype.risk_governor.risk_rules import _generate_rule_id, run_all_rules
from execution_prototype.risk_governor.governor import _generate_decision_id, make_governor_decision
from execution_prototype.risk_governor.cli import main as cli_main
import json

def test_deterministic_ids():
    t1 = _generate_trust_score_id({"a": 1})
    t2 = _generate_trust_score_id({"a": 1})
    assert t1 == t2
    
    r1 = _generate_rule_id("r1", "ev")
    r2 = _generate_rule_id("r1", "ev")
    assert r1 == r2
    
    d1 = _generate_decision_id("t1", "c1")
    d2 = _generate_decision_id("t1", "c1")
    assert d1 == d2

def _mock_data(overrides=None):
    overrides = overrides or {}
    candidates = overrides.get("candidates", [{"candidate_id": "c1", "metadata_present": True, "risk_flags": []}])
    paper_trades = overrides.get("paper_trades", [{"candidate_id": "c1"}])
    paper_decisions = overrides.get("paper_decisions", [{"action": "paper_enter", "validated_ledger_evidence": True, "confidence": "high", "metadata_present": True}])
    paper_review = overrides.get("paper_review", {"win_rate": 80.0, "losses": 0})
    early_warnings = overrides.get("early_warnings", [])
    strategy_backtests = overrides.get("strategy_backtests", [{"result_id": "b1"}])
    strategy_tournament = overrides.get("strategy_tournament", {"ranked_strategies": [{"risk_adjusted_score": 90, "unknown_outcome_rate": 10}]})
    return candidates, paper_trades, paper_decisions, paper_review, early_warnings, strategy_backtests, strategy_tournament

def _get_rules(data):
    return run_all_rules(data[0], data[2], data[3], data[4], data[6])

def test_allow_paper_high_score_no_criticals():
    data = _mock_data()
    trust = calculate_trust_score(*data)
    assert trust.confidence_band == "high"
    rules = _get_rules(data)
    decision = make_governor_decision(trust, rules, "camp1")
    assert decision.decision == "allow_paper"

def test_reduce_paper_risk_medium_score():
    data = _mock_data({
        "paper_decisions": [{"action": "paper_enter", "validated_ledger_evidence": True, "confidence": "high", "metadata_present": True, "reason": "AMBIGUOUS_MATCH"}]
    })
    trust = calculate_trust_score(*data)
    rules = _get_rules(data)
    decision = make_governor_decision(trust, rules, "camp1")
    assert decision.decision == "reduce_paper_risk" or decision.decision == "halt_paper"

def test_halt_paper_critical_drift():
    data = _mock_data({"early_warnings": [{"severity": "critical"}]})
    trust = calculate_trust_score(*data)
    rules = _get_rules(data)
    decision = make_governor_decision(trust, rules, "camp1")
    assert decision.decision == "halt_paper"
    assert "RULE_DRIFT_1" in decision.triggered_rules

def test_halt_paper_excessive_drawdown():
    data = _mock_data({"paper_review": {"win_rate": 10.0, "losses": 10}}) # losses > 5 fails DD rule
    trust = calculate_trust_score(*data)
    rules = _get_rules(data)
    decision = make_governor_decision(trust, rules, "camp1")
    assert decision.decision == "halt_paper"
    assert "RULE_DD_1" in decision.triggered_rules

def test_halt_paper_missing_metadata_domination():
    data = _mock_data({"candidates": [{"metadata_present": False}, {"metadata_present": False}]})
    trust = calculate_trust_score(*data)
    rules = _get_rules(data)
    decision = make_governor_decision(trust, rules, "camp1")
    assert decision.decision == "halt_paper"
    assert "RULE_META_1" in decision.triggered_rules

def test_halt_paper_unvalidated_entries():
    data = _mock_data({"paper_decisions": [{"action": "paper_enter", "validated_ledger_evidence": False}]})
    trust = calculate_trust_score(*data)
    rules = _get_rules(data)
    decision = make_governor_decision(trust, rules, "camp1")
    assert decision.decision == "halt_paper"
    assert "RULE_VAL_1" in decision.triggered_rules

def test_halt_paper_false_confidence():
    data = _mock_data({"paper_decisions": [{"action": "paper_enter", "confidence": "high", "metadata_present": False}]})
    trust = calculate_trust_score(*data)
    rules = _get_rules(data)
    decision = make_governor_decision(trust, rules, "camp1")
    assert decision.decision == "halt_paper"
    assert "RULE_CONF_1" in decision.triggered_rules

def test_insufficient_data():
    trust = calculate_trust_score([], [], [], None, [], [], None)
    rules = run_all_rules([], [], None, [], None)
    decision = make_governor_decision(trust, rules, "camp1")
    assert decision.decision == "insufficient_data"

def test_protocol_features_warning():
    data = _mock_data({"candidates": [{"metadata_present": True, "risk_flags": ["CLAWBACK_ENABLED"]}]})
    rules = _get_rules(data)
    prot_rule = next(r for r in rules if r.rule_id == "RULE_PROT_1")
    assert prot_rule.severity == "warning"
    assert "Clawback enabled" in str(prot_rule.evidence)

def test_live_readiness_always_forbidden():
    rules = _get_rules(_mock_data())
    live_rule = next(r for r in rules if r.rule_id == "RULE_LIVE_1")
    assert not live_rule.passed
    assert live_rule.severity == "critical"

def test_cli_dry_run(tmp_path, monkeypatch):
    p36 = tmp_path / "p36"
    p37 = tmp_path / "p37"
    out = tmp_path / "out"
    p36.mkdir()
    p37.mkdir()
    
    args = ["cli.py", "--phase36-report", str(p36), "--phase37-report", str(p37), "--output-dir", str(out), "--dry-run"]
    monkeypatch.setattr("sys.argv", args)
    
    try:
        cli_main()
    except SystemExit as e:
        assert e.code == 0
        
    assert not out.exists()
