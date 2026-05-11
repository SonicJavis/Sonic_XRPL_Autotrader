import json
from pathlib import Path

from sonic_xrpl.runtime_profile.conformance import evaluate_runtime_profile_conformance
from sonic_xrpl.runtime_profile.models import DETERMINISTIC_CREATED_AT, FAIL, REVIEW


FIXTURES = Path("tests/fixtures/runtime_profile")


def _load(name: str) -> dict[str, str]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_phase57_safe_paper_profile_is_not_fail():
    report = evaluate_runtime_profile_conformance(env=_load("paper_profile.json"), created_at=DETERMINISTIC_CREATED_AT)
    assert report.status in {"PASS", "REVIEW"}
    check_map = {item.check_id: item for item in report.checks}
    assert check_map["live_trading_disabled"].status == "PASS"
    assert check_map["execution_disabled"].status == "PASS"
    assert check_map["dry_run_enabled_for_paper"].status == "PASS"


def test_phase57_live_enabled_profile_fails():
    report = evaluate_runtime_profile_conformance(env=_load("unsafe_live_enabled_profile.json"), created_at=DETERMINISTIC_CREATED_AT)
    assert report.status == FAIL
    check_map = {item.check_id: item for item in report.checks}
    assert check_map["live_trading_disabled"].status == FAIL
    assert check_map["execution_disabled"].status == FAIL


def test_phase57_missing_env_profile_reviews():
    report = evaluate_runtime_profile_conformance(env=_load("missing_env_profile.json"), created_at=DETERMINISTIC_CREATED_AT)
    assert report.status in {REVIEW, FAIL}
    assert any(check.status == REVIEW for check in report.checks)
