from pathlib import Path

from sonic_xrpl.calibration_implementation_plan.planner import build_calibration_implementation_plan


APPROVAL = "reports/phase55/latest_calibration_approval_ledger.json"


def test_phase56_plan_keeps_all_safety_flags_false_or_blocked():
    plan = build_calibration_implementation_plan(
        APPROVAL,
        "tests/fixtures/calibration_implementation_plan/approved_change_requests.json",
    )
    assert plan.paper_only is True
    assert plan.offline_only is True
    assert plan.dry_run_only is True
    assert plan.auto_apply_allowed is False
    assert plan.live_execution_allowed is False
    assert plan.runtime_mutation_allowed is False
    assert plan.requires_human_implementation is True
    for item in plan.implementation_items:
        assert item.safety_flags["auto_apply_allowed"] is False
        assert item.safety_flags["live_execution_allowed"] is False
        assert item.safety_flags["runtime_mutation_allowed"] is False


def test_phase56_unsafe_change_request_is_blocked():
    plan = build_calibration_implementation_plan(
        APPROVAL,
        "tests/fixtures/calibration_implementation_plan/blocked_unsafe_change_request.json",
    )
    assert plan.implementation_items == ()
    assert len(plan.blocked_items) == 1
    assert plan.blocked_items[0].reason.startswith("unsafe_flag_")


def test_phase56_package_has_no_forbidden_execution_terms():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/calibration_implementation_plan").glob("*.py"))
    forbidden = [
        "submitAndWait",
        "autofill",
        "Xaman",
        "fromSeed",
        "familySeed",
        "auto-buy",
        "place_order",
        "while True",
        "websocket",
        "requests.get(",
        "requests.post(",
    ]
    for term in forbidden:
        assert term not in combined
