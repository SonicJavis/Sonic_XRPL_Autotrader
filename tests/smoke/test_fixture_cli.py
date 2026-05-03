"""Smoke tests for fixture CLI commands."""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC_DIR = str(_REPO_ROOT / "src")
FIXTURE_DIR = str(Path(__file__).parent.parent / "fixtures" / "xrpl")


def _run(*args):
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{_SRC_DIR}:{existing_pp}" if existing_pp else _SRC_DIR
    result = subprocess.run(
        [sys.executable, "-m", "sonic_xrpl.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    return result


def test_fixture_command_exists():
    result = _run("fixtures", "--path", FIXTURE_DIR)
    assert result.returncode == 0


def test_fixture_health_command():
    result = _run("fixture-health", "--path", FIXTURE_DIR)
    assert result.returncode == 0
    assert "HEALTHY" in result.stdout or "healthy" in result.stdout.lower()


def test_fixture_account_command():
    result = _run("fixture-account", "--path", FIXTURE_DIR, "--account", "rTrader")
    assert result.returncode == 0
    assert "rTrader" in result.stdout


def test_fixture_amm_command():
    result = _run("fixture-amm", "--path", FIXTURE_DIR, "--asset-a", "XRP", "--asset-b", "USD_rIssuer")
    assert result.returncode == 0


def test_fixture_balance_changes_command():
    metadata_path = str(Path(__file__).parent.parent / "fixtures" / "xrpl" / "metadata" / "payment_partial_metadata.json")
    result = _run("fixture-balance-changes", "--metadata", metadata_path)
    assert result.returncode == 0
