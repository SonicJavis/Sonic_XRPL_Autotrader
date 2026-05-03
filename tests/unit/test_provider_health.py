"""Tests for provider health checks."""
from __future__ import annotations
from pathlib import Path
import pytest
from sonic_xrpl.providers.health import check_fixture_health, HealthStatus, FixtureHealthReport

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl"


def test_healthy_fixture_dir():
    report = check_fixture_health(FIXTURE_DIR)
    assert report.status == HealthStatus.HEALTHY
    assert report.manifest_ok is True
    assert report.secret_scan_ok is True
    assert report.issues == []


def test_missing_fixture_dir(tmp_path):
    missing = tmp_path / "nonexistent"
    report = check_fixture_health(missing)
    assert report.status == HealthStatus.FIXTURE_MISSING
    assert report.manifest_ok is False
    assert len(report.issues) > 0


def test_degraded_if_dir_missing(tmp_path):
    # Create a valid manifest but no subdirs
    (tmp_path / "manifest.json").write_text('{"name":"x","version":"1","network":"test","ledger_min":1,"ledger_max":1}')
    report = check_fixture_health(tmp_path)
    assert report.status == HealthStatus.DEGRADED


def test_health_report_has_dirs_ok():
    report = check_fixture_health(FIXTURE_DIR)
    assert isinstance(report.dirs_ok, dict)
    assert "ledgers" in report.dirs_ok
