"""Tests for Phase 58A guard-critical file detection."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from guard_critical_changes import (  # noqa: E402
    CRITICAL_FILES,
    CRITICAL_PREFIXES,
    find_guard_critical_changes,
    is_guard_critical,
    _run_git_diff,
    main,
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


def test_run_git_diff_returns_files_from_three_dot() -> None:
    with patch("guard_critical_changes.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="a.py\nb.py\n", stderr="")
        changed = _run_git_diff("origin/main", "HEAD")
    assert changed == ["a.py", "b.py"]


def test_run_git_diff_falls_back_to_two_dot() -> None:
    with patch("guard_critical_changes.subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="bad three dot"),
            MagicMock(returncode=0, stdout="c.py\n", stderr=""),
        ]
        changed = _run_git_diff("origin/main", "HEAD")
    assert changed == ["c.py"]


def test_run_git_diff_missing_base_raises_clear_error() -> None:
    with patch("guard_critical_changes.subprocess.run") as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="unknown revision"),
            MagicMock(returncode=1, stdout="", stderr="unknown revision"),
            MagicMock(returncode=0, stdout="abc refs/remotes/origin/dev\n", stderr=""),
        ]
        with pytest.raises(RuntimeError) as exc:
            _run_git_diff("origin/main", "HEAD")
    message = str(exc.value)
    assert "base=origin/main" in message
    assert "head=HEAD" in message
    assert "available_refs=" in message
    assert "suggested_fix=" in message


def test_main_supports_base_head_aliases() -> None:
    with patch("guard_critical_changes._run_git_diff", return_value=["README.md"]):
        with patch.object(sys, "argv", ["guard_critical_changes.py", "--base", "origin/dev", "--head", "HEAD"]):
            rc = main()
    assert rc == 0
