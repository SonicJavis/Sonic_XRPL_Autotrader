import pytest
from pathlib import Path
from scripts.safety_grep import check_file

def test_safety_grep_rejects_unsafe_legacy_patterns(tmp_path):
    test_file = tmp_path / "bad_code.py"
    test_file.write_text("wallet = Wallet.from_seed(seed)\nsubmit_and_wait(tx)\nlive buy token")
    
    violations, allowed = check_file(test_file)
    assert len(violations) >= 3
    assert any("wallet" in v for v in violations)
    assert any("submit_and_wait" in v for v in violations)
    assert any("live buy" in v for v in violations)

def test_safety_grep_allows_whitelisted_strings(tmp_path):
    test_file = tmp_path / "safe_code.py"
    test_file.write_text("x = build_unsigned()\nfrom execution_prototype.submit import submit_manual")
    
    violations, allowed = check_file(test_file)
    assert len(violations) == 0
    assert len(allowed) == 1
    assert any("submit_manual" in a for a in allowed)
