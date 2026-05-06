import subprocess
import sys
from pathlib import Path


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "sonic_xrpl.cli.main", *args], text=True, capture_output=True, check=False)


def test_firstledger_signals_cli_offline_empty_state():
    result = run_cli("firstledger-signals", "--fixture", "tests/fixtures/firstledger/empty_candidates.json")
    assert result.returncode == 0
    assert "No source-backed FirstLedger launches available." in result.stdout
    assert "Live execution    : BLOCKED" in result.stdout


def test_firstledger_signals_cli_source_backed_limitations():
    result = run_cli("firstledger-signals", "--fixture", "tests/fixtures/firstledger/source_backed_candidates.json")
    assert result.returncode == 0
    assert "WATCH" in result.stdout
    assert "live_execution_allowed=False" in result.stdout
    assert "source-backed fixture" in result.stdout


def test_firstledger_signal_report_cli_writes_files(tmp_path):
    result = run_cli(
        "firstledger-signal-report",
        "--fixture",
        "tests/fixtures/firstledger/source_backed_candidates.json",
        "--output-dir",
        str(tmp_path),
    )
    assert result.returncode == 0
    assert (tmp_path / "firstledger_signals.json").exists()
    assert (tmp_path / "firstledger_signals.md").exists()
