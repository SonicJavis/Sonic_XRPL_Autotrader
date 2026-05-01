import pytest
import json
from pathlib import Path
from execution_prototype.backtest_datasets.loaders import DatasetLoader, get_deterministic_id
from execution_prototype.backtest_datasets.window_builder import WindowBuilder
from execution_prototype.backtest_datasets.splitter import DatasetSplitter
from execution_prototype.backtest_datasets.leakage_checks import LeakageChecker
from execution_prototype.backtest_datasets.quality_checks import QualityChecker

def test_deterministic_id():
    inputs1 = ["test", 123, {"a": 1}]
    inputs2 = ["test", 123, {"a": 1}]
    inputs3 = ["test", 123, {"a": 2}]
    
    id1 = get_deterministic_id(inputs1)
    id2 = get_deterministic_id(inputs2)
    id3 = get_deterministic_id(inputs3)
    
    assert id1 == id2
    assert id1 != id3

def test_chronological_split():
    splitter = DatasetSplitter()
    records = [
        {"ledger_index": 10, "observed_at": "2026-01-01T00:00:00Z"},
        {"ledger_index": 30, "observed_at": "2026-01-01T00:00:30Z"},
        {"ledger_index": 20, "observed_at": "2026-01-01T00:00:20Z"},
        {"ledger_index": 40, "observed_at": "2026-01-01T00:00:40Z"},
        {"ledger_index": 50, "observed_at": "2026-01-01T00:00:50Z"},
    ]
    
    # 60/20/20 of 5 records: 3, 1, 1
    split = splitter.split_chronologically(records, 0.6, 0.2, 0.2)
    
    assert len(split["train"]) == 3
    assert len(split["validation"]) == 1
    assert len(split["test"]) == 1
    
    # Check order
    assert split["train"][0]["ledger_index"] == 10
    assert split["train"][1]["ledger_index"] == 20
    assert split["train"][2]["ledger_index"] == 30
    assert split["validation"][0]["ledger_index"] == 40
    assert split["test"][0]["ledger_index"] == 50

def test_future_leakage():
    checker = LeakageChecker()
    # Case: Decision at ledger 20 references snapshot at ledger 30
    records = [
        {"type": "price_snapshot", "snapshot_id": "snap1", "ledger_index": 10},
        {"type": "candidate_score", "ledger_index": 20, "referenced_snapshots": ["snap2"]},
        {"type": "price_snapshot", "snapshot_id": "snap2", "ledger_index": 30},
    ]
    
    issues = checker.check_future_leakage(records)
    assert len(issues) == 1
    assert "Future Leakage" in issues[0]

def test_quality_score_penalties():
    checker = QualityChecker()
    # Case: Multiple issuers for same ticker
    records = [
        {"ticker": "MOON", "issuer": "issuer1", "asset_key": "K1"},
        {"ticker": "MOON", "issuer": "issuer2", "asset_key": "K2"},
    ]
    
    report = checker.generate_report("test_ds", records)
    assert report.quality_score <= 50 # Cap for ambiguous identity
    assert any("Ambiguous asset identity" in issue for issue in report.critical_issues)

def test_protocol_context_flags():
    checker = QualityChecker()
    records = [
        {"type": "tx", "unsupported_batch_context": True},
        {"type": "tx", "xahau_context": True},
    ]
    
    report = checker.generate_report("test_ds", records)
    assert report.unsupported_batch_context_count == 1
    assert report.xahau_hook_context_count == 1
    assert report.quality_score <= 60
