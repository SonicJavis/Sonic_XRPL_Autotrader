from __future__ import annotations

import json
import subprocess
import sys
from math import isfinite
from pathlib import Path

from scripts.xrpl_live_shadow_replay import run_fixture


FIXTURE = Path("data/live_shadow_replay_fixtures/phase23_basic.json")
STRESS_FIXTURE = Path("data/live_shadow_replay_fixtures/phase23_stress.json")


def test_live_replay_fixture_is_deterministic() -> None:
    first = run_fixture(FIXTURE)
    second = run_fixture(FIXTURE)

    assert first == second
    assert first["status"]["processed_ledger_count"] >= 1
    assert first["gap_count"] >= 1
    assert first["duplicate_count"] >= 1
    assert first["resolved_windows"] >= 1
    assert first["expired_windows"] >= 1
    assert _finite_json(first)


def test_live_replay_stress_fixture_remains_bounded() -> None:
    body = run_fixture(STRESS_FIXTURE)

    assert body["status"]["buffer_size"] <= 4
    assert body["status"]["processed_ledger_count"] <= 12
    assert body["status"]["duplicate_ledger_count"] >= 1
    assert _finite_json(body)


def test_replay_runner_cli_is_offline_and_json_stable() -> None:
    cmd = [sys.executable, "scripts/xrpl_live_shadow_replay.py", "--fixture", str(FIXTURE)]
    first = subprocess.run(cmd, check=True, capture_output=True, text=True)
    second = subprocess.run(cmd, check=True, capture_output=True, text=True)

    assert first.stdout == second.stdout
    body = json.loads(first.stdout)
    assert body["is_shadow"] is True
    assert body["is_executable"] is False
    assert "status" in body and "metrics" in body and "drift" in body


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True
