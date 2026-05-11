import subprocess
import sys


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "sonic_xrpl.cli.main", *args], text=True, capture_output=True, check=False)


def test_phase57_cli_help_includes_commands():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "runtime-profile" in result.stdout
    assert "runtime-profile-conformance" in result.stdout
    assert "runtime-profile-report" in result.stdout


def test_phase57_runtime_profile_command():
    result = run_cli("runtime-profile")
    assert result.returncode == 0, result.stderr
    assert "Phase 57 Runtime Profile" in result.stdout
    assert "Live execution     : BLOCKED" in result.stdout


def test_phase57_runtime_profile_conformance_command():
    result = run_cli("runtime-profile-conformance")
    assert result.returncode in {0, 1}, result.stderr
    assert "Phase 57 Runtime Profile Conformance" in result.stdout
    assert "live_trading_disabled" in result.stdout


def test_phase57_runtime_profile_report_command(tmp_path):
    result = run_cli("runtime-profile-report", "--output-dir", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "latest_runtime_profile.json").exists()
    assert (tmp_path / "latest_runtime_profile.md").exists()
    assert (tmp_path / "latest_runtime_profile_conformance.json").exists()
    assert (tmp_path / "latest_runtime_profile_conformance.md").exists()
