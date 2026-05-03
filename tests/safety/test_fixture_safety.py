"""Safety tests for fixture files."""
from __future__ import annotations
from pathlib import Path
from sonic_xrpl.audit.safety_scan import scan_fixture_files, SafetyClassification

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl"


def test_no_secrets_in_fixtures():
    findings = scan_fixture_files(FIXTURE_DIR)
    blocked = [f for f in findings if f.classification.value == "blocked"]
    assert blocked == [], f"Secret patterns found in fixtures: {blocked}"


def test_tessuccess_not_blocked():
    """tesSUCCESS must not be flagged as a secret."""
    findings = scan_fixture_files(FIXTURE_DIR)
    for f in findings:
        assert "tesSUCCESS" not in f.context or f.classification.value != "blocked"


def test_scan_missing_dir_returns_empty(tmp_path):
    missing = tmp_path / "no_such_dir"
    findings = scan_fixture_files(missing)
    assert findings == []
