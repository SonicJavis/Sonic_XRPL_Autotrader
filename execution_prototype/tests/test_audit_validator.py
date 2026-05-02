"""Tests for scripts/audit_validator.py (Phase 42.2).

These tests verify the audit validator's check functions in isolation.
They are written so they do NOT depend on the local git branch state or
any transient generated artifacts – only pure logic is exercised.
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure repo root is on sys.path so both scripts and execution_prototype are
# importable when pytest runs from any working directory.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.audit_validator import (
    REQUIRED_SAFETY_STRINGS,
    check_doc_disclosures,
    check_import_smoke,
    main,
)


# ---------------------------------------------------------------------------
# Report shape
# ---------------------------------------------------------------------------


def test_report_shape(tmp_path, monkeypatch):
    """The JSON report must include schema_version, overall_passed, and checks."""
    # Redirect artifacts to a temp dir so we do not clobber the real file.
    monkeypatch.setattr("scripts.audit_validator.ARTIFACTS_DIR", tmp_path)

    exit_code = main()

    report_path = tmp_path / "audit_validator_report.json"
    assert report_path.exists(), "Report file was not created"

    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert "schema_version" in report
    assert "overall_passed" in report
    assert "checks" in report
    assert isinstance(report["checks"], dict)
    assert "branch_hygiene" in report["checks"]
    assert "safety_grep" in report["checks"]
    assert "import_smoke" in report["checks"]
    assert "cli_help" in report["checks"]
    assert "doc_disclosures" in report["checks"]

    for check in report["checks"].values():
        assert "passed" in check
        assert "details" in check


# ---------------------------------------------------------------------------
# Documentation disclosure detection
# ---------------------------------------------------------------------------


def test_doc_disclosures_pass_with_required_strings(tmp_path, monkeypatch):
    """check_doc_disclosures passes when all required strings are present."""
    # Build synthetic docs that satisfy all requirements.
    required = {
        "docs/SYSTEM_STATE.md": ["paper-only", "0/100", "Fail-Closed"],
        "README.md": ["paper", "No wallet"],
    }
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "SYSTEM_STATE.md").write_text(
        "This system is paper-only. Live Trading: 0/100. Fail-Closed posture.",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text(
        "Paper trading only. No wallet. No signing.",
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.audit_validator.REPO_ROOT", tmp_path)
    monkeypatch.setattr("scripts.audit_validator.REQUIRED_SAFETY_STRINGS", required)

    result = check_doc_disclosures()
    assert result["passed"] is True
    assert result["details"]["failures"] == []


def test_doc_disclosures_fail_on_missing_string(tmp_path, monkeypatch):
    """check_doc_disclosures fails when a required string is absent."""
    required = {"README.md": ["No wallet", "paper-only"]}
    (tmp_path / "README.md").write_text(
        "This project uses paper trading only.",  # Missing "No wallet"
        encoding="utf-8",
    )

    monkeypatch.setattr("scripts.audit_validator.REPO_ROOT", tmp_path)
    monkeypatch.setattr("scripts.audit_validator.REQUIRED_SAFETY_STRINGS", required)

    result = check_doc_disclosures()
    assert result["passed"] is False
    assert any("No wallet" in f for f in result["details"]["failures"])


def test_doc_disclosures_fail_on_missing_file(tmp_path, monkeypatch):
    """check_doc_disclosures fails when a required file is absent."""
    required = {"docs/SYSTEM_STATE.md": ["paper-only"]}
    # Do NOT create the file.

    monkeypatch.setattr("scripts.audit_validator.REPO_ROOT", tmp_path)
    monkeypatch.setattr("scripts.audit_validator.REQUIRED_SAFETY_STRINGS", required)

    result = check_doc_disclosures()
    assert result["passed"] is False
    assert any("file not found" in f for f in result["details"]["failures"])


# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------


def test_import_smoke_fails_on_bad_module(monkeypatch):
    """check_import_smoke reports failures for non-existent modules."""
    monkeypatch.setattr(
        "scripts.audit_validator.PROTOTYPE_PACKAGES",
        ["execution_prototype", "execution_prototype.does_not_exist_xyz"],
    )

    result = check_import_smoke()
    assert result["passed"] is False
    assert result["details"]["failure_count"] == 1
    assert any("does_not_exist_xyz" in f for f in result["details"]["failures"])


def test_import_smoke_passes_for_real_packages():
    """check_import_smoke passes for the real execution_prototype packages."""
    # Only test the root package to keep this fast; the full list is covered by
    # the validator integration test (test_report_shape).
    from scripts.audit_validator import PROTOTYPE_PACKAGES, check_import_smoke

    # Temporarily narrow to just the root to avoid long import chains in testing.
    import scripts.audit_validator as av_module
    original = av_module.PROTOTYPE_PACKAGES
    av_module.PROTOTYPE_PACKAGES = ["execution_prototype"]
    try:
        result = check_import_smoke()
    finally:
        av_module.PROTOTYPE_PACKAGES = original

    assert result["passed"] is True
    assert result["details"]["failure_count"] == 0


# ---------------------------------------------------------------------------
# Banned pattern detection (via safety_grep check)
# ---------------------------------------------------------------------------


def test_safety_grep_check_passes_on_clean_run():
    """check_safety_grep passes on the actual repository (no forbidden patterns)."""
    from scripts.audit_validator import check_safety_grep

    result = check_safety_grep()
    assert result["passed"] is True, (
        f"Safety grep unexpectedly failed:\n{result['details'].get('stdout', '')}"
    )
