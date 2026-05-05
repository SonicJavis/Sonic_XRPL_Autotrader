import subprocess
import sys
from pathlib import Path

def test_fixture_health_command():
    """Test that the fixture health CLI command runs cleanly on Windows."""
    cmd = [sys.executable, "-m", "sonic_xrpl.cli.main"]
    
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
    assert any(phrase in (result.stdout or "") for phrase in ["HEALTHY", "[OK]", "Fixture"]), \
        f"Expected message not found. Got: {result.stdout}"
