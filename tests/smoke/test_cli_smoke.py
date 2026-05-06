import subprocess
import sys
from pathlib import Path


def test_cli_help_uses_real_v2_cli():
    """The root compatibility entrypoint must delegate to the real V2 CLI."""
    cmd = [sys.executable, "-m", "sonic_xrpl.cli.main", "--help"]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=Path(__file__).parent.parent.parent,
        timeout=10,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr or 'No stderr'}"
    stdout = result.stdout or ""
    assert "Sonic XRPL Autotrader V2" in stdout
    assert "safety-scan" in stdout


def test_cli_safety_scan():
    """Test safety scan command."""
    cmd = [sys.executable, "-m", "sonic_xrpl.cli.main", "safety-scan"]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=Path(__file__).parent.parent.parent,
        timeout=10,
    )
    
    assert result.returncode == 0, result.stderr or result.stdout
    assert "Safety scan passed" in (result.stdout or "")
