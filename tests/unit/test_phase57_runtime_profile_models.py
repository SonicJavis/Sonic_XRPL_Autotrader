import json
from pathlib import Path

from sonic_xrpl.runtime_profile.models import DETERMINISTIC_CREATED_AT
from sonic_xrpl.runtime_profile.profiles import build_runtime_profile_snapshot


FIXTURES = Path("tests/fixtures/runtime_profile")


def _load(name: str) -> dict[str, str]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_phase57_paper_profile_defaults_safe():
    profile = build_runtime_profile_snapshot(env=_load("paper_profile.json"), created_at=DETERMINISTIC_CREATED_AT)
    assert profile.profile_name == "paper"
    assert profile.paper_only is True
    assert profile.dry_run is True
    assert profile.live_execution_allowed is False
    assert profile.execution_enabled is False
    assert profile.signing_allowed is False
    assert profile.submission_allowed is False
    assert profile.wallet_material_allowed is False
    assert profile.dashboard_mutation_allowed is False
    assert profile.calibration_mutation_allowed is False
    assert profile.human_review_required is True


def test_phase57_profile_id_is_deterministic():
    env = _load("offline_profile.json")
    left = build_runtime_profile_snapshot(env=env, created_at=DETERMINISTIC_CREATED_AT)
    right = build_runtime_profile_snapshot(env=env, created_at=DETERMINISTIC_CREATED_AT)
    assert left.profile_id == right.profile_id


def test_phase57_unknown_profile_warns():
    profile = build_runtime_profile_snapshot(env=_load("missing_env_profile.json"), created_at=DETERMINISTIC_CREATED_AT)
    assert profile.profile_name == "unknown"
    assert "runtime_mode_unknown" in profile.warnings
