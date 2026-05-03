"""CLI smoke tests — verify all CLI commands work offline."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import pytest

# When running as a subprocess, ensure src/ is on PYTHONPATH
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SRC_DIR = str(_REPO_ROOT / "src")


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # Ensure src/ is on the subprocess's PYTHONPATH
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{_SRC_DIR}:{existing_pp}" if existing_pp else _SRC_DIR
    return subprocess.run(
        [sys.executable, "-m", "sonic_xrpl.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )


def test_cli_help():
    """CLI --help exits successfully."""
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "sonic_xrpl" in result.stdout.lower() or "COMMAND" in result.stdout


def test_cli_health():
    """CLI health command works offline."""
    result = _run_cli("health")
    assert result.returncode == 0
    assert "Mode" in result.stdout or "mode" in result.stdout


def test_cli_capabilities():
    """CLI capabilities command works offline."""
    result = _run_cli("capabilities")
    assert result.returncode == 0
    assert "AMM" in result.stdout


def test_cli_safety_scan():
    """CLI safety-scan command works offline."""
    result = _run_cli("safety-scan")
    # May return 0 (clean) or 1 (findings) — both are acceptable
    assert result.returncode in (0, 1)
    assert "Safety Scan" in result.stdout or "safety" in result.stdout.lower()


def test_cli_simulate_help():
    """CLI simulate --help works."""
    result = _run_cli("simulate", "--help")
    assert result.returncode == 0


def test_cli_reconcile_help():
    """CLI reconcile --help works."""
    result = _run_cli("reconcile", "--help")
    assert result.returncode == 0
