import pytest
from execution_prototype.paper_review.trade_journal import create_paper_trade
from execution_prototype.paper_review.performance_analyzer import analyze_performance
from execution_prototype.paper_review.models import PaperTradeHistory

def _mock_trade_kwargs():
    return {
        "campaign_id": "c1",
        "candidate_id": "cand1",
        "issuer": "rIss",
        "currency_code": "TOK",
        "entry_decision_id": "ed1",
        "entry_time": "t1",
        "entry_score": 50,
        "entry_score_band": "watch",
        "entry_reason": "test",
        "risk_flags_at_entry": [],
        "evidence_event_ids": [],
        "source_signal_types": ["trustline_created"],
        "metadata_present_at_entry": True,
        "validated_ledger_evidence": True,
        "amm_present": True,
        "liquidity_signal_strength": "strong",
        "paper_size_xrp": 100.0
    }

def test_unknown_outcome_if_price_missing():
    kwargs = _mock_trade_kwargs()
    # No prices
    trade = create_paper_trade(**kwargs)
    assert trade.outcome == "unknown"
    assert trade.paper_pnl_pct is None
    assert trade.paper_pnl_xrp is None
    assert "UNKNOWN_PRICE_OUTCOME" in trade.mistake_tags

def test_no_fake_pnl():
    kwargs = _mock_trade_kwargs()
    trade = create_paper_trade(**kwargs)
    assert trade.paper_pnl_xrp is None

def test_win_loss_breakeven_classification():
    k = _mock_trade_kwargs()
    
    # Win
    win_trade = create_paper_trade(entry_price_paper=10.0, exit_price_paper=15.0, **k)
    assert win_trade.outcome == "win"
    assert win_trade.paper_pnl_pct == 50.0
    
    # Loss
    loss_trade = create_paper_trade(entry_price_paper=10.0, exit_price_paper=5.0, **k)
    assert loss_trade.outcome == "loss"
    assert loss_trade.paper_pnl_pct == -50.0
    
    # Breakeven
    be_trade = create_paper_trade(entry_price_paper=10.0, exit_price_paper=10.0, **k)
    assert be_trade.outcome == "breakeven"
    assert be_trade.paper_pnl_pct == 0.0

def test_weak_metadata_creates_mistake_tag():
    k = _mock_trade_kwargs()
    k["metadata_present_at_entry"] = False
    trade = create_paper_trade(**k)
    assert "WEAK_METADATA_ENTRY" in trade.mistake_tags

def test_amm_backed_trade_creates_success_tag():
    k = _mock_trade_kwargs()
    trade = create_paper_trade(**k)
    assert "AMM_BACKED_ENTRY" in trade.success_tags

def test_offercreate_only_entry_remains_weak():
    k = _mock_trade_kwargs()
    k["source_signal_types"] = ["offer_activity_low_confidence"]
    k["amm_present"] = False
    trade = create_paper_trade(**k)
    assert "OFFER_ONLY_ENTRY" in trade.mistake_tags

def test_repeated_mistakes_detected():
    k = _mock_trade_kwargs()
    k["metadata_present_at_entry"] = False
    
    k1 = k.copy()
    k1["entry_decision_id"] = "e1"
    t1 = create_paper_trade(**k1)
    
    k2 = k.copy()
    k2["entry_decision_id"] = "e2"
    t2 = create_paper_trade(**k2)
    
    review = analyze_performance("c1", [t1, t2])
    assert "WEAK_METADATA_ENTRY" in review.repeated_mistakes

def test_best_worst_trade_selection():
    k = _mock_trade_kwargs()
    
    k1 = k.copy()
    k1["entry_price_paper"] = 10.0
    k1["exit_price_paper"] = 11.0
    k1["entry_decision_id"] = "e1"
    t1 = create_paper_trade(**k1)
    
    k2 = k.copy()
    k2["entry_price_paper"] = 10.0
    k2["exit_price_paper"] = 15.0
    k2["entry_decision_id"] = "e2"
    t2 = create_paper_trade(**k2)
    
    k3 = k.copy()
    k3["entry_price_paper"] = 10.0
    k3["exit_price_paper"] = 8.0
    k3["entry_decision_id"] = "e3"
    t3 = create_paper_trade(**k3)
    
    k4 = k.copy()
    k4["entry_price_paper"] = 10.0
    k4["exit_price_paper"] = 5.0
    k4["entry_decision_id"] = "e4"
    t4 = create_paper_trade(**k4)
    
    review = analyze_performance("c1", [t1, t2, t3, t4])
    assert review.best_trade_id == t2.trade_id
    assert review.worst_trade_id == t4.trade_id

def test_review_does_not_authorize_live_trading():
    k = _mock_trade_kwargs()
    t1 = create_paper_trade(**k)
    review = analyze_performance("c1", [t1])
    assert review.human_review_required is True
    assert "authorize live trading" in review.prohibited_auto_action
