"""Tests for Phase 58A guard-critical file detection."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from guard_critical_changes import (  # noqa: E402
    CRITICAL_FILES,
    CRITICAL_PREFIXES,
    find_guard_critical_changes,
    is_guard_critical,
)


def test_known_critical_files_include_safety_scripts() -> None:
    assert "scripts/safety_grep.py" in CRITICAL_FILES
    assert "scripts/audit_validator.py" in CRITICAL_FILES


def test_known_critical_prefixes_include_workflows_and_execution() -> None:
    assert ".github/workflows/" in CRITICAL_PREFIXES
    assert "src/sonic_xrpl/execution/" in CRITICAL_PREFIXES
    assert "app/execution/" in CRITICAL_PREFIXES


def test_is_guard_critical_true_for_prefix_match() -> None:
    assert is_guard_critical(".github/workflows/ci.yml")
    assert is_guard_critical("src/sonic_xrpl/execution/live_guard.py")


def test_is_guard_critical_true_for_exact_file_match() -> None:
    assert is_guard_critical("scripts/dependency_audit.py")


def test_is_guard_critical_false_for_non_critical_file() -> None:
    assert not is_guard_critical("src/sonic_xrpl/market/models.py")


def test_find_guard_critical_changes_filters_and_sorts() -> None:
    changed = [
        "src/sonic_xrpl/market/models.py",
        "scripts/audit_validator.py",
        ".github/workflows/safety-gate.yml",
        "README.md",
    ]
    result = find_guard_critical_changes(changed)
    assert result == [
        ".github/workflows/safety-gate.yml",
        "scripts/audit_validator.py",
    ]
